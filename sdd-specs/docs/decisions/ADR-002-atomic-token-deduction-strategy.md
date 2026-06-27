# ADR-002: Atomic Token Deduction Strategy

## Status
Accepted

## Date
2026-06-26

## Context
In the Prompt Arena workspace, players are allocated a strict token budget per game session. When players prompt the Google Gemini API proxy, their token usage (calculated from the upstream model's `usage_metadata`) must be deducted from their session budget stored in Supabase.

A naive update strategy would follow these steps:
1. Query the current token budget for the game session.
2. If remaining budget > 0, send the prompt to Gemini.
3. Receive the response and token count.
4. Calculate the new remaining budget.
5. Save the new budget to the database.

This naive approach is highly vulnerable to Time-of-Check to Time-of-Use (TOCTOU) race conditions. An attacker could issue multiple concurrent requests. Since the database read in step 1 happens concurrently before step 5 completes, multiple requests would see positive budgets, leading to excessive Gemini calls and token budget overruns (negative budgets).

We need a database-level atomic operation to decrement the budget and prevent parallel prompt requests from bypassing the token budget limit.

## Decision
We will implement an atomic token deduction function inside the PostgreSQL database using a PL/pgSQL stored procedure. We will call this function from FastAPI using the Supabase Python client's RPC (Remote Procedure Call) mechanism.

The database function signature:
```sql
CREATE OR REPLACE FUNCTION deduct_session_budget(session_id UUID, tokens_to_deduct INT)
RETURNS INT AS $$
DECLARE
    new_budget INT;
BEGIN
    UPDATE public.game_sessions
    SET token_budget = token_budget - tokens_to_deduct
    WHERE id = session_id AND token_budget >= tokens_to_deduct
    RETURNING token_budget INTO new_budget;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Insufficient token budget or session not found';
    END IF;
    
    RETURN new_budget;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

From FastAPI, we will invoke the RPC function:
```python
response = supabase.rpc("deduct_session_budget", {
    "session_id": str(session_id),
    "tokens_to_deduct": tokens
}).execute()
```

If the session's token budget is less than the requested deduction, the `UPDATE` query will affect 0 rows, throwing a database exception. The exception will be caught at the FastAPI API layer, returning an appropriate `403 Forbidden` response to the user.

## Alternatives Considered

### Python-Level Lock (asyncio.Lock or multiprocessing Lock)
- **Pros**: Easy to implement in Python.
- **Cons**: Only works within a single application process. Once the backend scales to multiple uvicorn workers or container replicas behind a load balancer, local locks cannot coordinate across processes.
- **Rejected**: Does not support horizontal scaling.

### Supabase Row-Level Locking (`SELECT FOR UPDATE`)
- **Pros**: Relies on PostgreSQL transaction locks.
- **Cons**: Locks rows during the duration of the API call, which includes the external slow Gemini API network call (up to 10 seconds). Keeping database transactions open during slow external I/O blocks connection pools and degrades performance.
- **Rejected**: Would cause connection pool exhaustion under load.

## Consequences
- Deductions are guaranteed to be atomic on the database engine.
- Parallel request exploits attempting to bypass the budget limit will be rejected database-side.
- The external Gemini API request is made *before* the database decrement, but validation is checked before the call. In the event of an upstream model call failure (e.g. rate limit, gateway error), no tokens are deducted since the database update is executed only after a successful Gemini response.
- The developer team must maintain database stored procedures using migration scripts in `supabase/migrations/`.
