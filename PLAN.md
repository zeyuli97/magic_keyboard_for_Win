# MacFlow implementation plan

1. Freeze interfaces and record environment. Status: interface v1 prepared; macOS host; Windows hardware NOT TESTED.
2. Implement isolated streams: profiles (B/C), lifecycle/discovery (A/D), QA (E), shared config/input/router (Lead).
3. Integrate, generate deterministic runtime configuration, run portable checks and review safety boundaries.
4. Assemble a development-preview Windows script package and manual checklist. No hardware gate is waived.

No drivers, elevated runtime, autorun or Kanata experiment is part of this iteration.
