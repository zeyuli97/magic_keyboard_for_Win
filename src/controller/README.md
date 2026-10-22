# Controller boundary

No separate controller is implemented or launched in this AHK development preview.
The tray and lifecycle live in `src/ahk/main.ahk`; its Native Mode / Quit controls
cover the only mapping process. Enable requires an explicit tray action on each
launch. There is no IPC listener, web service, network access or autorun.

A future multi-process backend needs a new reviewed contract for ownership,
heartbeats, disable acknowledgements, crash cleanup and whole-stack stop. A UI
that stops AHK alone must not claim to stop another backend. Do not add a dummy
controller or start a Kanata process under the current contract.
