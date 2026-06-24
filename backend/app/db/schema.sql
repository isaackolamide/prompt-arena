-- ==========================================
-- Prompt Arena - Core Database Schema
-- File: backend/app/db/schema.sql
-- ==========================================

-- Enable the UUID extension if not already enabled.
-- Supabase comes with uuid-ossp enabled by default, but this ensures compatibility.
create extension if not exists "uuid-ossp";

-- Mock Supabase Auth Schema & Users Table
-- During local development and testing, auth.users may not exist yet.
-- This ensures the schema script is executable on any PostgreSQL instance.
create schema if not exists auth;
create table if not exists auth.users (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    raw_user_meta_data jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Mock Supabase Auth uid() function if it doesn't exist (for local validation)
create or replace function auth.uid()
returns uuid
language sql stable
as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$;

-- ==========================================
-- DROP EXISTING TABLES (Re-runnable script)
-- ==========================================
drop table if exists public.scorecards cascade;
drop table if exists public.game_sessions cascade;
drop table if exists public.challenges cascade;
drop table if exists public.profiles cascade;

-- ==========================================
-- 1. PROFILES TABLE
-- ==========================================
-- Tracks user-specific data, gameplay metadata, and links to auth.users.
create table public.profiles (
    id uuid references auth.users(id) on delete cascade primary key,
    username text unique,
    display_name text,
    avatar_url text,
    
    -- Daily game rate-limiting variables
    daily_game_count integer default 0 not null,
    last_game_played_at timestamp with time zone,
    
    -- Audit timestamps
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Constraints
    constraint daily_game_count_nonnegative check (daily_game_count >= 0),
    constraint username_length check (username is null or char_length(username) >= 3),
    constraint username_format check (username is null or username ~* '^[a-zA-Z0-9_-]+$')
);

-- Enable RLS on Profiles
alter table public.profiles enable row level security;

-- Policies for Profiles
create policy "Allow public read access to profiles" 
    on public.profiles for select 
    using (true);

create policy "Allow users to update their own profile" 
    on public.profiles for update 
    using (auth.uid() = id);

-- ==========================================
-- 2. CHALLENGES TABLE
-- ==========================================
-- Stores prompt engineering challenges with their requirements, system prompt, and test cases.
create table public.challenges (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text not null,
    
    -- Core prompt engineering logic
    system_prompt text not null,
    initial_prompt text not null default '',
    
    -- JSON representation of evaluation inputs and expected outputs
    test_cases jsonb not null,
    
    -- Allowed token limit for input and output combined
    token_budget integer not null,
    
    difficulty text not null,
    
    -- Date this challenge is scheduled to be active. Unique ensures one challenge per day.
    scheduled_for date unique,
    
    -- Audit timestamps
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Constraints
    constraint title_not_empty check (char_length(title) > 0),
    constraint token_budget_positive check (token_budget > 0),
    constraint check_difficulty check (difficulty in ('easy', 'medium', 'hard'))
);

-- Enable RLS on Challenges
alter table public.challenges enable row level security;

-- Policies for Challenges
create policy "Allow public read access to challenges" 
    on public.challenges for select 
    using (true);

-- ==========================================
-- 3. GAME SESSIONS TABLE
-- ==========================================
-- Links players (profiles) to challenges they are currently playing or have completed.
create table public.game_sessions (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references public.profiles(id) on delete cascade,
    challenge_id uuid not null references public.challenges(id) on delete cascade,
    
    status text default 'in_progress' not null,
    
    -- Game session time boundaries
    started_at timestamp with time zone default timezone('utc'::text, now()) not null,
    ended_at timestamp with time zone,
    
    -- Audit timestamps
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Constraints
    constraint check_status check (status in ('in_progress', 'completed', 'failed', 'timed_out')),
    constraint ended_after_started check (ended_at is null or ended_at >= started_at),
    -- Prevent duplicate play attempts per challenge for the same user
    constraint unique_profile_challenge unique (profile_id, challenge_id)
);

-- Enable RLS on Game Sessions
alter table public.game_sessions enable row level security;

-- Policies for Game Sessions
create policy "Allow users to view their own game sessions" 
    on public.game_sessions for select 
    using (auth.uid() = profile_id);

-- ==========================================
-- 4. SCORECARDS TABLE
-- ==========================================
-- Stores the final submission metrics and evaluation results for completed game sessions.
create table public.scorecards (
    id uuid primary key default gen_random_uuid(),
    
    -- One scorecard per game session
    game_session_id uuid not null unique references public.game_sessions(id) on delete cascade,
    
    -- Denormalized references for easier querying and indexing
    profile_id uuid not null references public.profiles(id) on delete cascade,
    challenge_id uuid not null references public.challenges(id) on delete cascade,
    
    -- Individual scores out of 100
    score_correctness numeric(5,2) not null,
    score_efficiency numeric(5,2) not null,
    score_speed numeric(5,2) not null,
    score_total numeric(5,2) not null,
    
    -- Raw performance metrics
    tokens_used integer not null,
    execution_time_ms integer not null,
    
    -- Submitted player prompt/code
    code_submitted text not null,
    
    -- Detailed results for each test case
    test_results jsonb not null,
    
    -- Timestamp when the scorecard was finalized
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Constraints
    constraint check_score_correctness check (score_correctness >= 0.00 and score_correctness <= 100.00),
    constraint check_score_efficiency check (score_efficiency >= 0.00 and score_efficiency <= 100.00),
    constraint check_score_speed check (score_speed >= 0.00 and score_speed <= 100.00),
    constraint check_score_total check (score_total >= 0.00 and score_total <= 100.00),
    constraint check_tokens_used check (tokens_used >= 0),
    constraint check_execution_time check (execution_time_ms >= 0)
);

-- Enable RLS on Scorecards
alter table public.scorecards enable row level security;

-- Policies for Scorecards
create policy "Allow public read access to scorecards" 
    on public.scorecards for select 
    using (true);

-- ==========================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ==========================================
-- Create indexes on foreign keys to optimize joins and RLS queries. (Unique constraints create indexes automatically).
create index if not exists idx_game_sessions_profile_id on public.game_sessions(profile_id);
create index if not exists idx_game_sessions_challenge_id on public.game_sessions(challenge_id);
create index if not exists idx_scorecards_profile_id on public.scorecards(profile_id);
create index if not exists idx_scorecards_challenge_id on public.scorecards(challenge_id);

-- ==========================================
-- AUTOMATION & TRIGGERS
-- ==========================================

-- Helper: Automatically update updated_at on modify
create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$ language plpgsql security definer set search_path = pg_catalog, public;

-- Helper: Prevent client-side updates to read-only profile columns (tampering checks)
create or replace function public.prevent_profile_tampering()
returns trigger as $$
begin
    -- Only restrict authenticated/anon users connecting via client APIs (PostgREST)
    if nullif(current_setting('request.jwt.claim.role', true), '') in ('authenticated', 'anon') then
        if new.daily_game_count is distinct from old.daily_game_count or
           new.last_game_played_at is distinct from old.last_game_played_at or
           new.id is distinct from old.id or
           new.created_at is distinct from old.created_at then
            raise exception 'Cannot modify read-only profile columns';
        end if;
    end if;
    return new;
end;
$$ language plpgsql security definer set search_path = pg_catalog, public;

-- Attach updated_at triggers
create trigger set_profiles_updated_at
    before update on public.profiles
    for each row execute procedure public.set_updated_at();

create trigger check_profiles_tampering
    before update on public.profiles
    for each row execute procedure public.prevent_profile_tampering();

create trigger set_challenges_updated_at
    before update on public.challenges
    for each row execute procedure public.set_updated_at();

create trigger set_game_sessions_updated_at
    before update on public.game_sessions
    for each row execute procedure public.set_updated_at();

-- Trigger: Automatically provision a profile when a new user signs up via Supabase Auth
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, username, display_name, avatar_url, daily_game_count)
    values (
        new.id,
        coalesce(
            new.raw_user_meta_data->>'username', 
            substring(new.email from '^[^@]+'), 
            'user_' || substring(new.id::text from 1 for 8)
        ),
        new.raw_user_meta_data->>'display_name',
        new.raw_user_meta_data->>'avatar_url',
        0
    );
    return new;
end;
$$ language plpgsql security definer set search_path = public;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();
