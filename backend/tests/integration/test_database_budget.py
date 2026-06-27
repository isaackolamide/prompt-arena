"""Integration tests verifying token budget updates atomically, constraints are enforced, and RPC exceptions are correctly thrown."""

import json
from typing import Any, Dict
from uuid import UUID, uuid4

import psycopg2
import pytest
from postgrest.exceptions import APIError
from supabase import Client

# Define Mock RPC Builder and Client as required
class MockResponse:
    def __init__(self, data: Any):
        self.data = data

class MockRPCBuilder:
    def __init__(self, conn_str: str, name: str, params: Dict[str, Any]):
        self.conn_str = conn_str
        self.name = name
        self.params = params

    def execute(self) -> MockResponse:
        conn = psycopg2.connect(self.conn_str)
        try:
            with conn:
                with conn.cursor() as cur:
                    param_placeholders = ", ".join(f"{k} => %s" for k in self.params.keys())
                    query = f"SELECT {self.name}({param_placeholders});"
                    cur.execute(query, tuple(self.params.values()))
                    row = cur.fetchone()
                    data = row[0] if row else None
                    return MockResponse(data)
        except psycopg2.Error as e:
            message = getattr(e, "pgerror", str(e))
            code = "P0001"
            details = None
            hint = None
            if hasattr(e, "diag") and e.diag:
                message = e.diag.message_primary or message
                code = e.diag.sqlstate or code
                details = e.diag.message_detail
                hint = e.diag.message_hint
            raise APIError({
                "message": message,
                "code": code,
                "details": details,
                "hint": hint,
            })
        finally:
            conn.close()

class MockClient(Client):
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        super().__init__("https://mock.supabase.co", "mock-key")

    def rpc(self, name: str, params: Dict[str, Any]) -> MockRPCBuilder:
        return MockRPCBuilder(self.conn_str, name, params)

@pytest.fixture
def db_client(postgres_test_db: str) -> Client:
    """Fixture returning our MockClient wrapper around the PostgreSQL test database."""
    return MockClient(postgres_test_db)


# Helper functions to setup and query test database state
def setup_game_session(conn_str: str, budget: int) -> UUID:
    """Inserts a profile, challenge, and game session, returning the session_id."""
    conn = psycopg2.connect(conn_str)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            user_id = uuid4()
            meta_data = json.dumps({
                "username": f"user_{uuid4().hex[:8]}",
                "display_name": "Test User",
            })
            cur.execute(
                "INSERT INTO auth.users (id, email, raw_user_meta_data) VALUES (%s, %s, %s);",
                (str(user_id), f"{user_id}@example.com", meta_data),
            )
            
            challenge_id = uuid4()
            test_cases = json.dumps([{"input": "in", "expected": "out"}])
            cur.execute(
                """
                INSERT INTO public.challenges (
                    id, title, description, system_prompt, initial_prompt,
                    test_cases, token_budget, difficulty
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    str(challenge_id),
                    "Test Challenge",
                    "Description",
                    "System prompt",
                    "Initial prompt",
                    test_cases,
                    1000,
                    "easy",
                ),
            )
            
            session_id = uuid4()
            cur.execute(
                """
                INSERT INTO public.game_sessions (id, profile_id, challenge_id, status, token_budget)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (str(session_id), str(user_id), str(challenge_id), "in_progress", budget),
            )
            return session_id
    finally:
        conn.close()


def get_session_budget(conn_str: str, session_id: UUID) -> int:
    """Queries the current budget of a session directly."""
    conn = psycopg2.connect(conn_str)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT token_budget FROM public.game_sessions WHERE id = %s;", (str(session_id),))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def test_deduct_session_budget_success(db_client: Client) -> None:
    session_id = setup_game_session(db_client.conn_str, 100)
    response = db_client.rpc(
        "deduct_session_budget",
        {"session_id": str(session_id), "tokens_to_deduct": 30}
    ).execute()
    
    # 1. Verify returned new budget is 70
    assert response.data == 70
    
    # 2. Verify budget is updated to 70 in database
    assert get_session_budget(db_client.conn_str, session_id) == 70


def test_deduct_session_budget_insufficient(db_client: Client) -> None:
    session_id = setup_game_session(db_client.conn_str, 50)
    
    # 1. Verify that deducting more than available budget successfully caps the budget at 0
    response = db_client.rpc(
        "deduct_session_budget",
        {"session_id": str(session_id), "tokens_to_deduct": 60}
    ).execute()
    
    assert response.data == 0
    
    # 2. Verify budget is updated to 0 in database
    assert get_session_budget(db_client.conn_str, session_id) == 0


def test_deduct_session_budget_negative(db_client: Client) -> None:
    session_id = setup_game_session(db_client.conn_str, 50)
    
    # Verify that calling RPC with negative tokens raises a database exception (APIError)
    with pytest.raises(APIError) as exc_info:
        db_client.rpc(
            "deduct_session_budget",
            {"session_id": str(session_id), "tokens_to_deduct": -10}
        ).execute()
        
    assert "Tokens to deduct must be non-negative" in exc_info.value.message


def test_deduct_session_budget_missing(db_client: Client) -> None:
    non_existent_id = uuid4()
    
    # 1. Verify that calling with nonexistent session ID raises APIError
    with pytest.raises(APIError) as exc_info:
        db_client.rpc(
            "deduct_session_budget",
            {"session_id": str(non_existent_id), "tokens_to_deduct": 10}
        ).execute()
        
    assert "Session not found" in exc_info.value.message
