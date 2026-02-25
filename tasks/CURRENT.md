# CURRENT — Job Fair Polish Sprint (NO NEW FEATURES)

## Goal (one sentence)
Make the repository job-fair-ready: clean, reproducible, well-documented, and easy to explain in 2 minutes — without changing protocol/crypto/core behavior.

## Project Snapshot
Secure MQTT telemetry simulator:
Satellite (Raspberry Pi + BME280) → HMAC-SHA256 signing → MQTT → Ground Station → dedup → freshness/anti-replay → signature verify → routing (processed/rejected/quarantine).

Status:
- Working end-to-end
- 52 tests passing
- Runs on Raspberry Pi
- macOS dev environment uses Python 3.13 (Homebrew)

## Hard STOP Rules (must obey)
STOP and ask before proceeding if a change would:
- change MQTT topics, payload/envelope schema, protocol format
- change crypto primitives, signing/verifying semantics, key handling meaning
- change routing semantics (processed/rejected/quarantine meaning)
- add new runtime dependencies
- restructure core flow in a way that changes behavior

Allowed:
- docs/README/demo instructions
- repo hygiene (.gitignore, remove tracked artifacts)
- moving sample files to examples/ or tests/fixtures (behavior unchanged)
- renaming/moving docs files and updating links
- comment language normalization (German) where safe
- Do not introduce new tooling (black/ruff/pre-commit). Only use tools already configured in repo and keep diffs minimal.

## Mandatory constraints (repo-specific)
- Do not invent new run commands. Use existing scripts in `scripts/`:
  - `./scripts/satellite_start.sh` / `_status.sh` / `_stop.sh`
  - `./scripts/ground_start.sh` / `_status.sh` / `_stop.sh`
- MQTT broker for local demo: `docker compose -f docker-compose.mqtt.yml up -d`
- Tests must pass with: `pytest`
- Target Python: 3.13 (document it). Do not ship venv in repo.

## Acceptance Criteria
- Professional `README.md` with Quickstart, diagram, security features, and clear value.
- Clean repo: no tracked venv/logs/runtime data.
- No secrets in repo. Configs safe for public sharing.
- `pytest` passes.
- Added German project description + 2-minute pitch (docs file).

---

# Execution Plan

## 0) Baseline checks (show results)
Run and report outputs:
- `git status --porcelain`
- `pytest` (if too slow, at least run at the end; but prefer baseline + final)
- List tracked suspicious artifacts:
  - `git ls-files | grep -E '^(\\.venv/|venv/|\\.pytest_cache/|logs/|data/|.*\\.csv$|.*\\.log$|.*\\.jsonl$)' || true`

Secrets scan (DO NOT print secrets, only filenames + line numbers):
- `grep -RInE '(HMAC|SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY|KEY=|mqtt.*pass|passwd)' configs ground satellite shared || true`

If any real secret is found:
- replace with placeholder
- add documentation how to provide it via env / local config (no new dependencies)

## 1) Repo hygiene (must do)
### 1.1 Update root `.gitignore`
Ensure it ignores:
- `.venv/`, `venv/`
- `.pytest_cache/`, `__pycache__/`, `*.pyc`
- `.vscode/`, `.run/`, `.DS_Store`
- runtime: `logs/`, `data/**` (keep `.gitkeep` only)
- generated artifacts: `*.log`, `*.csv`, `*.jsonl`

### 1.2 Remove tracked artifacts from git index (do not delete local files)
If any are tracked, run:
- `git rm -r --cached .pytest_cache .venv venv logs || true`
- `git rm -r --cached data/tmp data/raw data/processed data/quarantine data/rejected data/archive || true`
- `git rm --cached test_data_telemetry.csv || true`

### 1.3 Ensure `data/` is clean and intentional
Keep only folder structure with `.gitkeep`:
- `data/raw/.gitkeep`
- `data/processed/.gitkeep`
- `data/quarantine/.gitkeep`
- `data/rejected/.gitkeep`
- `data/archive/.gitkeep`
- `data/reports/.gitkeep` (optional)

Do not keep real telemetry CSVs in `data/` (runtime only).

## 2) Create `examples/` for demo (must do)
Create `examples/` with small, safe demo files.
Move/rename if present:
- `data/tmp/good.csv` → `examples/telemetry_good.csv`
- `data/tmp/bad_sig.csv` → `examples/telemetry_bad_sig.csv`
- `data/tmp/corrupted.csv` → `examples/telemetry_corrupted.csv`
- `test_data_telemetry.csv` → either `examples/` or `tests/fixtures/` (choose based on usage)

Update any references in code/tests if necessary. Behavior must remain unchanged.

## 3) Docs cleanup and re-linking (must do)
Goal: high-signal docs for interviewers.

Create/ensure these files exist:
- `docs/architecture.md`
- `docs/security.md`
- `docs/demo.md`
- `docs/pitch_de.md`

If content exists under `docs/design/`:
- move it to the above filenames (or copy + delete old)
- update internal links accordingly

Keep `docs/mission_reports/` as “engineering log” (secondary).

## 4) README Rewrite Specification (German, professional tone)

Rewrite README.md completely.

Language: German.
Tone: technisch, präzise, kein Marketing, keine Rollenspiel-Elemente.

Structure must be:

1. Titel + 1-Satz-Zusammenfassung
   - End-to-end abgesicherte Telemetrie-Pipeline (Satellite → MQTT → Ground)
   - Fokus: Integrität, Replay-Resistenz, klare Architektur

2. Was dieses Projekt demonstriert (Bullet Points)
   - End-to-end Systemdesign
   - HMAC-SHA256 Integritätsschutz
   - Deduplication
   - Freshness / Anti-Replay
   - Routing (processed / rejected / quarantine)
   - Testabdeckung
   - Betrieb auf Raspberry Pi

3. Systemarchitektur (ASCII Diagramm)
   - Satellite
   - MQTT Transport
   - Ground Station
   - shared/ Layer (crypto + protocol)

4. Sicherheitsmodell
   Present as Threat → Control table:
   - Payload Manipulation → HMAC
   - Replay → Freshness + Sliding Window
   - Duplicate Messages → Dedup
   - Repeated Invalid Attempts → Lockout

5. Design Decisions
   - Warum HMAC (symmetrisch, performant, Integritätsfokus)
   - Warum klare Modultrennung (satellite/ ground/ shared/)
   - Warum Tests auf mehreren Ebenen

6. Schnellstart (macOS, Python 3.13)
   - python3.13 -m venv .venv
   - docker compose -f docker-compose.mqtt.yml up -d
   - use existing scripts from scripts/
   - pytest
   - Quickstart must use scripts/ground_*.sh and scripts/satellite_*.sh (no direct python module invocation).

   Do not invent commands.

7. Projektstruktur (real tree excerpt)

8. Teststrategie
   - Anzahl der Tests (use real number from pytest)
   - Unit / Integration / Security Tests

9. Grenzen & Annahmen
   - Demo-Umgebung
   - Shared Secret in Config
   - Kein vollständiges Produktions-Secret-Management

Remove:
- Mission Timeline
- Rollenspiel-Elemente
- Outdated dates
- Inconsistent claims

## 5) German description + 2-min pitch (must do)
Write `docs/pitch_de.md` containing:
- Kurzbeschreibung (3–6 Sätze)
- 2-Minuten Elevator Pitch (spoken style)

## 6) Code comment normalization (German, explain WHY)
Scope:
- `ground/src/ground/**/*.py`
- `satellite/src/satellite/**/*.py`
- `shared/src/shared/**/*.py`

Rules:
- Comments in German, professional tone
- Remove redundant comments that describe obvious code
- Keep comments explaining reasoning, security assumptions, edge cases
- Do not touch core logic or tests unless required for consistency
- Only change comments/docstrings. No refactoring, no renaming, no reformatting code lines.

## 7) Final verification and report (mandatory)
- Run `pytest`
- Show `git status --porcelain`
- Provide a clear summary:
  - files changed/added/removed
  - what was cleaned and why
  - confirm no protocol/crypto/core flow changes
  - confirm tests passing

---

# Deliverable Checklist (must be true at the end)
- [ ] README.md is job-fair-ready
- [ ] docs/architecture.md, docs/security.md, docs/demo.md exist and are linked
- [ ] docs/pitch_de.md exists
- [ ] .gitignore prevents venv/logs/runtime data from being tracked
- [ ] no tracked venv/logs/runtime csv/jsonl
- [ ] pytest passes