# Kanata experiment gate

**Not selected, not implemented, not started.** The current delivery uses a
single standard-user AHK v2 process. There is intentionally no active Kanata
configuration, executable, driver installer or startup command here.

Before any future backend experiment, Lead must approve an interface revision
that records an exact Kanata version, Windows input backend, its dependencies,
event ownership and handoff to AHK. Passing config validation is not evidence
that multiple keyboard hooks coexist safely. Neither this directory nor a
future experiment authorizes driver installation, registry/security changes,
elevation or autorun.

A separate experiment must measure left/right Command and physical Control,
USB/Bluetooth reconnects, Chinese IME/layout bypass, editor/terminal focus,
synthetic-loop avoidance, Command+Tab held-state cleanup, and whole-stack
Disable/Quit after either process fails. Keep evidence separate from the AHK
prototype. Adoption requires explicit scope and acceptance changes; it cannot
become a fallback automatically when an AHK action is blocked.
