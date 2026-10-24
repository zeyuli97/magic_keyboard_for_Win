# MacFlow implementation plan

1. DONE — Freeze interfaces and record environment. Interface v1; macOS host; Windows hardware NOT TESTED.
2. DONE — Implement and integrate isolated streams: profiles (B/C), lifecycle/discovery (A/D), QA (E), shared config/input/router (Lead).
3. DONE — Generate deterministic runtime configuration, run portable checks and review input ownership, session/power interruption and fail-closed configuration boundaries.
4. DONE — Assemble the development-preview source package, Windows smoke script, manual checklist and evidence format. No hardware gate is waived.
5. PARTIAL — Local Windows AHK 2.0.19 x64 syntax, Native initialization and Native registration/cleanup checks passed on 2026-10-23. USB Magic Keyboard physical-input tests remain pending; no hardware PASS is claimed. See docs/test-report.md for the tested scope.
6. BLOCKED — Resolve Windows Terminal selection/no-selection copy (prototype P0), Command+L and recycle-bin-only Explorer deletion (v1 P1) before claiming the corresponding gates.

No drivers, elevated runtime, autorun or Kanata experiment is part of this iteration.

Review follow-up: application/action validation and Python/AHK parity tightened; integration-era skips removed; Native registration self-check implemented; Git-indexed reproducible packaging and a separate pinned Windows CI job added. Scope/IME/passthrough policy and all release gates remain unchanged. Windows CI execution and hardware tests are still pending.
