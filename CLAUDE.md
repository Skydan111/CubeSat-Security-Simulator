# CLAUDE.md — CubeSat Security Simulator

This file defines non-negotiable working rules for Claude Code.
If any instruction conflicts with this file → STOP and ask.

---

## 1. Execution Commands (Source of Truth)

### Environment
- Activate venv (if present): `source .venv/bin/activate`

### Tests (required before proposing "done")
- `pytest`

### MQTT Broker (local demo)
- Start: `docker compose -f docker-compose.mqtt.yml up -d`
- Stop: `docker compose -f docker-compose.mqtt.yml down`

### Preferred Run Method
Use provided scripts. Do NOT invent alternatives.

Satellite:
- Start: `./scripts/satellite_start.sh`
- Status: `./scripts/satellite_status.sh`
- Stop: `./scripts/satellite_stop.sh`

Ground:
- Start: `./scripts/ground_start.sh`
- Status: `./scripts/ground_status.sh`
- Stop: `./scripts/ground_stop.sh`

---

## 2. Branch Policy (Learning Mode)

- NEVER commit directly to `main`.
- All changes MUST be in a feature branch.
- If currently on `main` → STOP and switch branch first.

---

## 3. Security Guardrails (Non-Negotiable)

- NEVER bypass or weaken:
  - signature verification
  - replay protection
  - freshness checks
- NEVER write, print, or commit secrets/keys.
- No secrets in repo, logs, tests, or documentation.
- If verification fails → route to `rejected` or `quarantine`.
- NEVER auto-accept invalid messages.

Security constraints override convenience.

---

## 4. Architectural Boundaries

- `shared/` → source of truth for protocol and crypto formats.
- `satellite/` → telemetry generation + publishing ONLY.
- `ground/` → verification + routing + analysis ONLY.
- DO NOT mix responsibilities across modules.

If a change impacts protocol, crypto, or routing semantics → update design docs or explain why not.

---

## 5. Dependency Discipline

- DO NOT mix dependencies between `satellite/`, `ground/`, `shared/`.
- DO NOT restructure packaging (`pyproject.toml`) unless explicitly requested.
- DO NOT add dependencies unless strictly required.
  If proposing a new dependency:
  - justify it,
  - provide a no-dependency alternative.

---

## 6. Change Discipline

- Prefer minimal, localized diffs.
- Avoid refactors unless explicitly requested.
- If behavior changes → update/add tests.
- Existing tests must remain meaningful.
- “Done” requires:
  - All tests pass (`pytest`)
  - Acceptance criteria in `tasks/CURRENT.md` satisfied

---

## 7. Task Scope Control

- Active execution scope is defined ONLY in `tasks/CURRENT.md`.
- Historical tasks live in `tasks/archive/`.
- `tasks/archive/` must not redefine architecture.
- If `CURRENT.md` conflicts with design docs → STOP and ask.

Before coding:
- Propose a short plan (3–8 bullets).

After coding:
- Show modified file list.
- Explain what changed and why.
- Prefer diff summaries for non-trivial changes.

Default mode:
- Conservative
- Security-first
- Minimal scope