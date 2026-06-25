import os
import sys
import time
from typing import Generator
import docker
import psycopg2
import pytest

# Add the parent 'backend' directory to sys.path so 'app' can be imported directly
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def run_migrations_on_test_db(conn_str: str) -> None:
    """Reads migration SQL and applies it to the temporary PostgreSQL database."""
    # Bootstrap mock auth schema first, as Supabase migrations assume auth.users and auth.uid() exist
    mock_auth_sql = """
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE TABLE IF NOT EXISTS auth.users (
        id UUID PRIMARY KEY,
        email TEXT,
        raw_user_meta_data JSONB
    );
    CREATE OR REPLACE FUNCTION auth.uid() RETURNS UUID AS $$
        SELECT null::UUID;
    $$ LANGUAGE SQL STABLE;
    """

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    migration_dir = os.path.join(base_dir, "supabase", "migrations")

    migration_files = []
    if os.path.exists(migration_dir):
        migration_files = sorted([
            f for f in os.listdir(migration_dir) if f.endswith(".sql")
        ])

    conn = psycopg2.connect(conn_str)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(mock_auth_sql)
            for file_name in migration_files:
                file_path = os.path.join(migration_dir, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    migration_sql = f.read()
                cur.execute(migration_sql)
    finally:
        conn.close()


@pytest.fixture(scope="session")
def postgres_test_db() -> Generator[str, None, None]:
    """Spawns a temporary postgres:17-alpine Docker container,

    applies Supabase migrations, yields the database connection string,
    and tears down the container on completion.
    """
    client = docker.from_env()

    # Run the container with a random host port mapping
    container = client.containers.run(
        "postgres:17-alpine",
        detach=True,
        ports={"5432/tcp": None},
        environment={
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_DB": "postgres",
        },
        auto_remove=False,
    )

    try:
        # Wait for pg_isready to pass inside the container
        max_retries = 30
        for _ in range(max_retries):
            exit_code, _ = container.exec_run("pg_isready -U postgres -d postgres")
            if exit_code == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("PostgreSQL container failed to become ready.")

        # Get the dynamically assigned host port
        container.reload()
        ports = container.attrs["NetworkSettings"]["Ports"]
        host_port = ports["5432/tcp"][0]["HostPort"]

        conn_str = f"postgresql://postgres:postgres@localhost:{host_port}/postgres"

        # Verify host connection is accessible
        for _ in range(20):
            try:
                conn = psycopg2.connect(conn_str)
                conn.close()
                break
            except psycopg2.OperationalError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Failed to connect to PostgreSQL container from host.")

        # Run migrations
        run_migrations_on_test_db(conn_str)

        yield conn_str

    finally:
        container.stop()
        container.remove()
