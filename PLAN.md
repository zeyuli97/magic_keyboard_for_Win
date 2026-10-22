# MacFlow implementation plan

1. DONE — Freeze interfaces and record environment. Interface v1; macOS host; Windows hardware NOT TESTED.
2. DONE — Implement and integrate isolated streams: profiles (B/C), lifecycle/discovery (A/D), QA (E), shared config/input/router (Lead).
3. DONE — Generate deterministic runtime configuration, run portable checks and review input ownership, session/power interruption and fail-closed configuration boundaries.
4. DONE — Assemble the development-preview source package, Windows smoke script, manual checklist and evidence format. No hardware gate is waived.
5. PENDING WINDOWS — Run installed AHK syntax/Native initialization checks, then actual Magic Keyboard tests; record environment and evidence. No AHK execution or hardware PASS is claimed.
6. BLOCKED — Resolve Windows Terminal selection/no-selection copy (prototype P0), Command+L and recycle-bin-only Explorer deletion (v1 P1) before claiming the corresponding gates.

No drivers, elevated runtime, autorun or Kanata experiment is part of this iteration.
