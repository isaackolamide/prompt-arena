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
    update public.game_sessions
    set token_budget = token_budget - tokens_to_deduct
    where id = session_id and token_budget >= tokens_to_deduct
    returning token_budget into new_budget;
    
    if not found then
        raise exception 'Insufficient token budget or session not found';
    end if;
    
    return new_budget;
end;
$$ language plpgsql security definer set search_path = public;
