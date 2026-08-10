# 9. Web UI ships both as a native Tauri app and a containerized page

**Status:** Accepted — 2026-08-07

## Context

The Web UI needs a distribution model. A plain containerized page (opened in a browser) is the default given the "everything is a container" deployment story. A native desktop app was also considered, for a more "installed product" feel and closer OS integration.

## Decision

Both, from the same Vite/React bundle, neither replacing the other: **Tauri** packages it as a native installable app (the preferred distribution channel); the existing Nginx-in-a-container option remains available.

## Rationale

Electron was considered and rejected: it would add a second, heavy packaging/distribution pipeline (per-OS installers, code signing, auto-update infrastructure) on top of the already-decided Docker distribution story, for a footprint (~80-120MB, bundling Chromium) that's hard to justify for a dev-tooling app with no heavy-media requirement. Tauri achieves the same "installed app" outcome using the system WebView, with an installer around 5-15MB, and is the current recommendation specifically for internal developer-tooling apps like TARS.

Whether the UI runs as a native app or a browser tab is independent of where the backend runs — it does not, by itself, imply support for a hosted/cloud backend (see `docs/architecture/security.md`'s note on connection direction).

## Consequences

- Both distribution paths talk to the same local Orchestrator the same way (SSE on `127.0.0.1`); the Orchestrator's port must be published to the host in `docker-compose.yml` so a natively-installed process outside the Compose network can reach it.
- `web/src-tauri/` exists alongside the regular Vite build output — CI only builds/publishes the Tauri installer (and Docker images) on release tags, not every push (`docs/adr/0010-...`, CI section).
- Web UI development still targets a single React codebase; Tauri-specific code should stay minimal and isolated to `src-tauri/`.
