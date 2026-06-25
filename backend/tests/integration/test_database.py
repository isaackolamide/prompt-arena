"""Integration tests verifying database schema, inserts, and queries."""

import json
from uuid import UUID, uuid4
import psycopg2
from psycopg2.extras import RealDictCursor


def test_postgres_test_db_schema_and_operations(postgres_test_db: str) -> None:
    """Verifies that we can connect, run schema migrations, insert, and select data."""
    conn = psycopg2.connect(postgres_test_db, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            # 1. Insert a mock user into auth.users with raw_user_meta_data
            user_id: UUID = uuid4()
            meta_data: str = json.dumps({
                "username": "testuser",
                "display_name": "Test User",
                "avatar_url": "http://example.com/avatar.png",
            })
            cur.execute(
                """
                INSERT INTO auth.users (id, email, raw_user_meta_data)
                VALUES (%s, %s, %s);
                """,
                (str(user_id), "test@example.com", meta_data),
            )

            # 2. Verify that the handle_new_user trigger automatically created the profile
            cur.execute(
                """
                SELECT id, username, display_name, daily_game_count
                FROM public.profiles WHERE id = %s;
                """,
                (str(user_id),),
            )
            profile_row = cur.fetchone()
            assert profile_row is not None
            assert UUID(profile_row["id"]) == user_id
            assert profile_row["username"] == "testuser"
            assert profile_row["display_name"] == "Test User"
            assert profile_row["daily_game_count"] == 0

            # 3. Update the profile and verify it works
            cur.execute(
                """
                UPDATE public.profiles
                SET display_name = %s
                WHERE id = %s
                RETURNING display_name;
                """,
                ("Updated Test User", str(user_id)),
            )
            updated_profile_row = cur.fetchone()
            assert updated_profile_row is not None
            assert updated_profile_row["display_name"] == "Updated Test User"

            # 4. Insert a challenge
            challenge_id: UUID = uuid4()
            test_cases_json: str = json.dumps([{"input": "hello", "expected": "world"}])
            cur.execute(
                """
                INSERT INTO public.challenges (
                    id, title, description, system_prompt, initial_prompt,
                    test_cases, token_budget, difficulty
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, title, token_budget, difficulty;
                """,
                (
                    str(challenge_id),
                    "System Test",
                    "A test challenge for integration checking.",
                    "You are a helpful assistant.",
                    "Say hello",
                    test_cases_json,
                    1000,
                    "easy",
                ),
            )
            challenge_row = cur.fetchone()
            assert challenge_row is not None
            assert UUID(challenge_row["id"]) == challenge_id
            assert challenge_row["title"] == "System Test"
            assert challenge_row["token_budget"] == 1000
            assert challenge_row["difficulty"] == "easy"

            # 5. Verify we can select the profiles and challenges and they join correctly
            # (e.g. creating a dummy game session linking them)
            session_id: UUID = uuid4()
            cur.execute(
                """
                INSERT INTO public.game_sessions (id, profile_id, challenge_id, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id, status;
                """,
                (str(session_id), str(user_id), str(challenge_id), "in_progress"),
            )
            session_row = cur.fetchone()
            assert session_row is not None
            assert UUID(session_row["id"]) == session_id
            assert session_row["status"] == "in_progress"

    finally:
        conn.close()
