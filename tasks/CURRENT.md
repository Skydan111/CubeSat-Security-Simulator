# CURRENT.md — Active Task Queue

Last updated: 2026-03-30

-----

## 🔴 HIGH PRIORITY — Security Fixes

### TASK-01: Fail-secure for dummy SecurityManager [SELF]

**File:** `ground/src/ground/receiver.py`
**Problem:** `try_import_secman()` returns a DummySecman that silently
allows everything — system runs without a security layer without any warning.
**Fix:** If SecurityManager fails to import — raise RuntimeError, no fallback.
**Definition of done:** System refuses to start without a real SecurityManager.
**Tests:** `pytest tests/unit/ground/`

-----

### TASK-02: Remove hardcoded “deadbeef” default secret [SELF]

**Files:**

- `ground/src/ground/mqtt_subscriber.py`
- `satellite/src/satellite/mqtt_publisher.py`
- `scripts/ground_start.sh`
  **Problem:** Hardcoded default makes HMAC verification meaningless.
  **Fix:** If `HMAC_SECRET_HEX` is not set — raise explicit error on startup.
  **Definition of done:** System fails with a clear message if variable is missing.
  **Tests:** `pytest tests/unit/`

-----

### TASK-03: Context manager for SecurityManager [SELF]

**File:** `ground/src/ground/security/security_manager.py`
**Problem:** `__del__` does not guarantee audit file is closed on crash.
**Fix:** Implement `__enter__` and `__exit__` methods.
**Definition of done:** SecurityManager is used via `with` statement.
**Tests:** `pytest tests/unit/ground/security/`

-----

## 🟡 MEDIUM PRIORITY — Architecture

### TASK-04: bme280.py returns TelemetryUnsigned directly [SELF]

**File:** `satellite/src/satellite/sensors/bme280.py`
**Problem:** `read()` returns a plain dict — manual conversion happens in `logger.py`.
**Fix:** `read()` returns `TelemetryUnsigned` directly.
**Definition of done:** Manual conversion in `logger.py` is removed, all tests green.
**Tests:** `pytest tests/unit/satellite/`

-----

### TASK-05: Remove duplicate HMAC logic in verify.py [SELF]

**File:** `ground/src/ground/verify.py`
**Problem:** HMAC logic is duplicated — `shared/crypto/hmac_sha256.py`
must be the single source of truth.
**Fix:** `verify.py` delegates to `shared`, no own implementation.
**Definition of done:** Duplicate code removed, all tests green.
**Important:** Check via tests what is actually being called before removing anything.
**Tests:** `pytest tests/unit/`

-----

### TASK-06: Direct path in receiver.py bypasses security checks [TOGETHER]

**File:** `ground/src/ground/receiver.py`
**Problem:** `receive_from_file()` and `receive_from_stdin()` do not use
`MqttMessageGuard` — no dedup or freshness checks.
**Fix:** Make `MqttMessageGuard` available to the direct path as well.
**Definition of done:** Both paths enforce the same security checks.
**Tests:** `pytest tests/integration/ground/`

-----

### TASK-07: Standardize configuration approach [TOGETHER]

**Files:** `satellite/src/satellite/logger.py`, all scripts
**Problem:** Some files read JSON config, others use environment variables.
**Fix:** Single approach — `.env` file + `.gitignore` entry.
**Definition of done:** All modules use one consistent configuration mechanism.
**Tests:** `pytest`

-----

## 🟢 LOW PRIORITY — Code Quality

### TASK-08: Remove dead mqtt_publisher.py [SELF]

**File:** `satellite/src/satellite/mqtt_publisher.py`
**Fix:** Delete or explicitly label as standalone demo tool.
**Definition of done:** `satellite_start.sh` still works correctly.

-----

### TASK-09: Extract lockout logic into helper function [TOGETHER]

**File:** `ground/src/ground/receiver.py`
**Problem:** Lockout block is duplicated in `handle_line()`
and `handle_verified_line()`.
**Fix:** Extract into private function `_handle_lockout()`.

-----

### TASK-10: Split receiver.py into focused modules [TOGETHER]

**File:** `ground/src/ground/receiver.py`
**Problem:** 4 distinct responsibilities in one file.
**Fix:** Split into `file_ops.py`, `pipeline.py`, `input_adapters.py`, `cli.py`.

-----

### TASK-11: Remove duplication in plot.py [SELF]

**File:** `ground/src/ground/plot.py`
**Fix:** Extract private helper `_draw_charts(axes, df)`.

-----

### TASK-12: Remove dead commented code in logger.py [SELF]

**File:** `satellite/src/satellite/logger.py`
**Fix:** Delete commented-out lines at the top of the file.

-----

### TASK-13: Standardize process invocation in scripts [SELF]

**File:** `scripts/satellite_start.sh`
**Problem:** Logger is started via `python -m`, publisher via direct file path.
**Fix:** Both use `python -m module` style.

-----

## ✅ COMPLETED

<!-- Move finished tasks here after pytest passes and Definition of done is met -->