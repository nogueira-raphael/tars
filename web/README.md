# web

React + TypeScript, built with Vite, packaged both as a Tauri native app and as a container-served page (Nginx) — see `/docs/adr/0009-web-ui-tauri-and-container-distribution.md`.

**Not scaffolded yet.** This is the last service in the build order (`/docs/architecture/domain-model.md`) — it depends on the Orchestrator↔Web UI API contract, which is itself deferred until `services/orchestrator` is being built. When that contract exists, scaffold this directory with the actual Vite/React/Tauri tooling (`pnpm create vite`, `pnpm tauri init`) rather than hand-authoring the tree; don't invent the API client or feature structure ahead of that contract.

Planned layout once scaffolded (`/docs/architecture/domain-model.md`):

```
web/src/
├── features/{chat,connections,plan-viewer,schema-explorer,approvals}/
├── shared/       # shadcn/ui components, design tokens, API client
└── app/          # routing, providers, entry point
web/src-tauri/     # Tauri native shell
```
