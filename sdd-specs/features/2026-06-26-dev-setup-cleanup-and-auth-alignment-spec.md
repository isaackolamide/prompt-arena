# Feature Spec: dev-setup-cleanup-and-auth-alignment

## Objective
Optimize the local Supabase development environment by disabling unused services (Realtime, Storage, Edge Functions) to reduce resource overhead. Align the frontend application with the invite-only magic link/OTP authentication model defined in `sdd-specs/mission.md`, replacing the password signup/login forms. Upgrade the UI/UX to a premium, glassmorphic dark-theme design suited for a competitive coding game.

## User & Stakeholder
* **Developers**: Benefit from a lightweight Docker development footprint with faster startup/shutdown times.
* **Players (Invited Software Engineers)**: Experience a frictionless, secure invite-only sign-in process via magic link OTPs on a visually stunning web interface.

## Acceptance Criteria
* **Given** a developer runs `make start`, **When** the Supabase local emulator boots up, **Then** only the essential services (`db`, `api`, `auth`, `local_smtp`, `studio`) are started, and `realtime`, `storage`, `imgproxy`, and `edge-runtime` containers are not spawned.
* **Given** a player visits the Prompt Arena home screen, **When** they view the authentication interface, **Then** they are presented with a premium, responsive glassmorphic dark-mode panel featuring modern typography, animated status states, and distinct interactive feedback.
* **Given** a player signing up or signing in, **When** they submit their email, **Then** they receive an OTP email (captured in the local Inbucket dev console) and are redirected to a code-entry verification screen.
* **Given** the player submits the correct OTP code, **When** the verification is processed, **Then** they are authenticated into the application without ever supplying or managing a password.

## Technical Constraints
* **Compile-Time Correctness**: Maintain strict TypeScript typing in the frontend, preventing any usage of the `any` escape hatch.
* **Backend Safety**: Ensure Pydantic schemas in the FastAPI routes strictly validate incoming email structures.
* **UI Performance**: Vanilla CSS styles must render efficiently without external layout framework dependencies.

## In Scope
* Modify `supabase/config.toml` to disable `realtime`, `storage` (and its S3/image sub-properties), and `edge_runtime`.
* Revise `frontend/src/App.tsx` to completely remove email/password registration and sign-in forms.
* Implement a state-based Magic Link Request and Verification flow (Email Input -> Code Verification Input) in `frontend/src/App.tsx`.
* Design a premium glassmorphic dark UI system in `frontend/src/App.tsx` using customized HSL variables, backdrop filters, clean border glows, and micro-animations for input focus and button states.
* Integrate frontend API requests with `/api/auth/magic-link` and `/api/auth/verify` endpoints.

## Out of Scope
* Implementing game sandbox execution (AWS Lambda/Firecracker integration).
* Implementing game timer logic, session storage persistence, or scoring formulas.
* Design of the leaderboard or public scoreboards.

## Dependencies
* `supabase/config.toml` (configuration)
* `frontend/src/App.tsx` (interface & client state)
* `backend/app/api/auth.py` (authentication endpoints)

## Stakeholder Flags
* **none** (Invited signup is already aligned with the Core Mission in `sdd-specs/mission.md`)

## Success Metrics
* Total container footprint spawned by `make start` reduced by 4 containers (Realtime, Storage, Imgproxy, Edge Functions runtime).
* Verified magic link / OTP sign-in flow successfully creates local profile rows in the `profiles` table.
