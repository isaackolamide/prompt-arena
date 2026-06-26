-- Migration: Add token_budget column to game_sessions and deduct_session_budget stored function
-- File: supabase/migrations/20260626000000_add_game_sessions_token_budget.sql

-- 1. Add token_budget column to public.game_sessions
alter table public.game_sessions
add column token_budget integer not null default 0,
add constraint token_budget_nonnegative check (token_budget >= 0);

-- 2. Create deduct_session_budget stored function
create or replace function public.deduct_session_budget(session_id uuid, tokens_to_deduct int)
returns int as $$
declare
    new_budget int;
begin
    if tokens_to_deduct < 0 then
        raise exception 'Tokens to deduct must be non-negative';
    end if;

    update public.game_sessions
    set token_budget = greatest(0, token_budget - tokens_to_deduct)
    where id = session_id
    returning token_budget into new_budget;
    
    if not found then
        raise exception 'Session not found';
    end if;
    
    return new_budget;
end;
$$ language plpgsql security definer set search_path = public;

-- 3. Revoke execute privileges from public, anon, and authenticated roles
do $$
begin
    if not exists (select from pg_catalog.pg_roles where rolname = 'anon') then
        create role anon;
    end if;
    if not exists (select from pg_catalog.pg_roles where rolname = 'authenticated') then
        create role authenticated;
    end if;
end
$$;

revoke execute on function public.deduct_session_budget(uuid, int) from public;
revoke execute on function public.deduct_session_budget(uuid, int) from anon;
revoke execute on function public.deduct_session_budget(uuid, int) from authenticated;

-- 4. Implement prevent_session_tampering function and trigger
create or replace function public.prevent_session_tampering()
returns trigger as $$
begin
    if nullif(current_setting('request.jwt.claim.role', true), '') in ('authenticated', 'anon') then
        if new.token_budget is distinct from old.token_budget or
           new.status is distinct from old.status then
            raise exception 'Cannot modify read-only session columns directly';
        end if;
    end if;
    return new;
end;
$$ language plpgsql security definer set search_path = pg_catalog, public;

create trigger check_session_tampering
    before update on public.game_sessions
    for each row execute procedure public.prevent_session_tampering();

