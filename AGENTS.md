# MacFlow development

This repository implements the Google Doc specification at https://docs.google.com/document/d/1GlBcn8PpgCiUHCXzl3kUaBjWpS909ThDqEknYTjjow4 (revision captured 2026-10-22).

- Delivery is DEVELOPMENT PREVIEW until all required Windows + Magic Keyboard tests pass. Never report Python/static checks as AHK runtime or hardware success.
- Never install drivers, edit keyboard/security registry, elevate the runtime, enable autorun (start at sign-in is off by default; only the user's tray choice turns it on), record input/clipboard contents, or access the network at runtime.
- Keep physical Control and right Command native. Unknown application/layout/integrity is bypassed. Start in Native Mode.
- Contracts in docs/contracts.md are authoritative for implementation. Propose interface changes to Lead first.
- Implementation streams use isolated worktrees, one owner per file. Lead integrates. No remote push is authorized.
- For this initial implementation, roles B/C are one profiles stream; A/D are one lifecycle stream; E owns QA. Lead owns shared routing/configuration/build/CI. Roles may be sequenced; five simultaneous agents are not required.
- Profiles: src/ahk/{global,terminal,browser,explorer}.ahk, config/{mappings,apps}.yaml, integrations/.
- Lifecycle/discovery: src/ahk/{main,emergency}.ahk, tools/inspect-keys.ps1, docs/{rollback,environment,input-discovery}.md, src/{controller,kanata}/.
- QA: tests/, tools/{macflow_config,validate-config}.py, tools/smoke-tests.ps1, docs/{compatibility-matrix,test-report}.md, README.md.
- Lead: all other files, including schema, release scope, config loader, input/router, generator, packaging and CI.
- Run `python3 tools/validate-config.py`, `python3 tools/generate-config.py --check`, and `python3 -m unittest discover -s tests -p 'test_*.py'` before integration. Windows checks are separate.

