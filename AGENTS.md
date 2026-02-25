# CubeSat Security Simulator (AGENTS.md)

---

## Commands (source of truth)

### Environment
- Activate venv (if present): `source .venv/bin/activate`

### Tests (required before proposing "done")
- `pytest`

### MQTT broker (for local demo if required)
- Start broker: `docker compose -f docker-compose.mqtt.yml up -d`
- Stop broker: `docker compose -f docker-compose.mqtt.yml down`

### Run (preferred method)
- Start Satellite: `./scripts/satellite_start.sh`
- Satellite status: `./scripts/satellite_status.sh`
- Stop Satellite: `./scripts/satellite_stop.sh`

- Start Ground: `./scripts/ground_start.sh`
- Ground status: `./scripts/ground_status.sh`
- Stop Ground: `./scripts/ground_stop.sh`

### Rule
- Do not invent alternative run commands.
- Prefer `scripts/` and the provided docker-compose file.

---

## Branch Policy (learning mode)

- All changes MUST be made in a feature branch.
- Never commit directly to `main`.
- If currently on `main`, STOP and switch branches first.

---

## Guardrails (non-negotiable)

- Never bypass or weaken signature verification, replay protection, or freshness checks.
- Never write, print, or commit secrets/keys.
- No secrets in repo, logs, tests, or docs.
- If verification fails → route to `rejected` or `quarantine`.
- Do NOT "auto-accept" invalid messages.

---

## Project Boundaries

- `shared/` is source-of-truth for protocol and crypto formats.
- `satellite/` → telemetry generation + publishing only.
- `ground/` → verification + routing + analysis only.
- No mixing responsibilities between modules.

---

## Dependency Boundaries

- Do not mix dependencies between `satellite/`, `ground/`, `shared/`.
- Do not restructure packaging (`pyproject.toml`) unless explicitly requested.
- Do not add dependencies unless strictly required and justified.

---

## Change Discipline

- Prefer minimal, localized diffs.
- Avoid refactors unless explicitly requested.
- If behavior changes → update/add tests.
- Keep existing tests meaningful.

---

## Design Documentation

Long-term system design lives in:

`docs/design/`

Includes:
- protocol description
- security model
- architecture overview

If a task affects protocol, crypto, or routing rules:
- Update the relevant design document
OR
- Explain why no update is required.

Design docs define stable system behavior.
Tasks must not silently redefine architecture.

---

## Task Management

- Active execution scope is defined ONLY in `tasks/CURRENT.md`.
- Historical tasks live in `tasks/archive/`.
- `tasks/archive/` must not redefine system architecture.
- If `CURRENT.md` conflicts with design docs → STOP and ask.
- "Done" means:
  - All tests pass (`pytest`)
  - Acceptance criteria in `CURRENT.md` are satisfied.

---

## Working Protocol (Collaboration Rules)

Before coding:
- Propose a short plan (3–8 bullets) based on `tasks/CURRENT.md`.

After coding:
- Show modified file list.
- Briefly explain what changed and why.
- Prefer diff summaries for non-trivial changes.

Default mode:
- Conservative
- Security-first
- Minimal scope