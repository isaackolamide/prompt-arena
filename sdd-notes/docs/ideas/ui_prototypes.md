# Prompt Arena MVP: UI & Workspace Paradigms

This document presents the visual prototypes and workspace paradigms generated for the Prompt Arena MVP to help refine the product direction.

````carousel
# Option 1: Monaco Side-by-Side Diff Viewer
![Monaco Diff UI Mockup](/Users/isaac-bp/.gemini/antigravity-ide/brain/c016b9f9-5186-4d02-a4ea-e0700f15239f/monaco_diff_viewer_ui_1783178237499.png)
- **Concept**: Split-screen with a file explorer + prompt sidebar on the left, and a side-by-side Monaco diff viewer on the right.
- **Pros**: Clear visual feedback on LLM changes; feels like a professional IDE.
- **Cons**: High initial implementation complexity for web Monaco integrations.
<!-- slide -->
# Option 2: Local IDE CLI Agent (Developer-First)
![Local IDE CLI Mockup](/Users/isaac-bp/.gemini/antigravity-ide/brain/c016b9f9-5186-4d02-a4ea-e0700f15239f/local_ide_cli_agent_ui_1783178280962.png)
- **Concept**: Play in your actual local editor (VS Code/Cursor). A local CLI utility manages state, pulls challenges, prompts the LLM, and runs tests.
- **Pros**: Zero web editor front-end work; developers use tools they love.
- **Cons**: High friction to set up locally; hard to spec/replay visually on the web.
<!-- slide -->
# Option 3: Dual-Pane Web CLI (Retro-Modern Terminal)
![Web CLI UI Mockup](/Users/isaac-bp/.gemini/antigravity-ide/brain/c016b9f9-5186-4d02-a4ea-e0700f15239f/dual_pane_web_cli_ui_1783178253591.png)
- **Concept**: Split terminal-like interface. Left: terminal file tree and read-only text file viewers. Right: interactive bash command terminal.
- **Pros**: Fits the "hacker" aesthetic; easy to implement using simple CSS/monospaced fonts.
- **Cons**: Text-based diffs must be rendered manually using terminal colors.
<!-- slide -->
# Option 4: Prompt-as-a-Service UI (Simple Chat Layout)
![Prompt Service UI Mockup](/Users/isaac-bp/.gemini/antigravity-ide/brain/c016b9f9-5186-4d02-a4ea-e0700f15239f/prompt_service_chat_ui_1783178267476.png)
- **Concept**: Three-column dashboard. Left: File Explorer & Active File. Middle: ChatGPT-like conversational assistant window. Right: Visual test suite execution panel.
- **Pros**: Cleanest and most accessible layout for non-technical or casual spectators.
- **Cons**: Diverges slightly from the raw "terminal/IDE" feel.
<!-- slide -->
# Option 5: Time-Attack Dashboard / Leaderboard
![Time-Attack Dashboard Mockup](/Users/isaac-bp/.gemini/antigravity-ide/brain/c016b9f9-5186-4d02-a4ea-e0700f15239f/time_attack_dashboard_ui_1783178294204.png)
- **Concept**: Dashboard tracking execution stats and real-time ghost graphs comparing player credit consumption vs. baseline AI.
- **Pros**: Highly competitive and gamified.
- **Cons**: Requires backend orchestration to cache and stream ghost trajectories.
````

---

### Core Questions for Next Phase:
1. **Which combination of workspace layout (Options 1–4) and competition engine (Option 5) do you want to lock in for the refined PRD?**
2. **Would you like me to proceed with Phase 2 (Evaluate & Converge) using the Monaco Diff Viewer + Time-Attack Dashboard as the baseline, or do you prefer one of the lighter-weight terminal/chat paradigms?**
