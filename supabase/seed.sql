-- ==========================================
-- Prompt Arena - Database Seeds
-- File: supabase/seed.sql
-- ==========================================

-- Clear existing data
TRUNCATE auth.users CASCADE;
TRUNCATE public.challenges CASCADE;

-- Insert Mock Auth Users
-- Password is pre-hashed bcrypt of 'password123'
-- The trigger public.handle_new_user() will automatically insert corresponding profiles into public.profiles.
INSERT INTO auth.users (
  id, 
  instance_id, 
  aud, 
  role, 
  email, 
  encrypted_password, 
  email_confirmed_at, 
  raw_app_meta_data, 
  raw_user_meta_data, 
  created_at, 
  updated_at, 
  confirmation_token, 
  recovery_token, 
  email_change_token_new, 
  email_change
)
VALUES
  (
    '00000000-0000-0000-0000-000000000001', 
    '00000000-0000-0000-0000-000000000000', 
    'authenticated', 
    'authenticated', 
    'alice@example.com', 
    '$2a$10$tQ1NWT7c4tQyv2kH85PzcuHl39VdK1L/Z9eWc/oK4/U0n6d04r43q', 
    now(), 
    '{"provider": "email", "providers": ["email"]}', 
    '{"username": "alice", "display_name": "Alice", "avatar_url": "https://api.dicebear.com/7.x/adventurer/svg?seed=Alice"}', 
    now(), 
    now(), 
    '', 
    '', 
    '', 
    ''
  ),
  (
    '00000000-0000-0000-0000-000000000002', 
    '00000000-0000-0000-0000-000000000000', 
    'authenticated', 
    'authenticated', 
    'bob@example.com', 
    '$2a$10$tQ1NWT7c4tQyv2kH85PzcuHl39VdK1L/Z9eWc/oK4/U0n6d04r43q', 
    now(), 
    '{"provider": "email", "providers": ["email"]}', 
    '{"username": "bob", "display_name": "Bob", "avatar_url": "https://api.dicebear.com/7.x/adventurer/svg?seed=Bob"}', 
    now(), 
    now(), 
    '', 
    '', 
    '', 
    ''
  );

-- Insert Mock Challenges
-- We schedule them for yesterday, today, and tomorrow.
INSERT INTO public.challenges (
  id, 
  title, 
  description, 
  system_prompt, 
  initial_prompt, 
  test_cases, 
  token_budget, 
  difficulty, 
  scheduled_for
)
VALUES
  (
    '11111111-1111-1111-1111-111111111111',
    'The Emoji Translator',
    'Translate the given English text into emojis. Be creative and concise.',
    'You are an Emoji Translator. Translate the user input into emojis only. Do not respond with any text other than emojis.',
    'Translate this: hello world',
    '[{"input": "I love coding", "expected": "❤️💻"}, {"input": "Happy birthday", "expected": "🎉🎂"}]'::jsonb,
    100,
    'easy',
    CURRENT_DATE - INTERVAL '1 day'
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    'SQL Query Generator',
    'Generate a single SQL query based on the English description. Only output the raw SQL, no markdown.',
    'You are an SQL generator. Output only a valid PostgreSQL query. No explanations, no markdown code blocks.',
    'Select all users who registered in the last 30 days.',
    '[{"input": "Select user with id 5", "expected": "SELECT * FROM users WHERE id = 5;"}]'::jsonb,
    200,
    'medium',
    CURRENT_DATE
  ),
  (
    '33333333-3333-3333-3333-333333333333',
    'Reverse Turing Test',
    'Convince the AI evaluator that you are a machine. The evaluator will ask questions, and you must respond in a way that is indistinguishable from a simple compiler/interpreter.',
    'You are a compiler. Only output syntax error or compilation successful. Do not talk like a human.',
    'Calculate 5 + 5',
    '[{"input": "print(\"hello\")", "expected": "compilation successful"}]'::jsonb,
    150,
    'hard',
    CURRENT_DATE + INTERVAL '1 day'
  );
