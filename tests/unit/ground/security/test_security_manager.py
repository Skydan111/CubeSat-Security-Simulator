import json
import time as pytime
import pytest

from ground.security.security_manager import SecurityManager


def write_policy(tmp_path, **overrides):
    """
    Пишем минимальную YAML policy в tmp_path и возвращаем путь.
    Даёт нам контроль над порогами (без влияния реального configs/).
    """
    policy = {
        "window_seconds": 120,
        "max_fail_ratio": 0.4,
        "min_events_in_window": 10,
        "consecutive_fail_threshold": 5,
        "lockout_seconds": 60,
        "cooldown_seconds": 90,
        "action_during_lockout": "quarantine",
        "weights": {
            "invalid_signature": 1.0,
            "corrupt_payload": 0.6,
            "malformed_packet": 0.8,
        },
        "security_log_path": str(tmp_path / "logs" / "security.log"),
        "audit_log_path": str(tmp_path / "logs" / "security_audit.jsonl"),
    }
    policy.update(overrides)

    p = tmp_path / "policy.yaml"
    # yaml-safe писать строкой — ок, но лучше как настоящий YAML:
    import yaml
    p.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
    return str(p), policy


def read_audit_lines(audit_path):
    if not audit_path.exists():
        return []
    txt = audit_path.read_text(encoding="utf-8").strip()
    if not txt:
        return []
    return [json.loads(line) for line in txt.splitlines()]


@pytest.fixture
def sm(tmp_path):
    policy_path, _ = write_policy(tmp_path)
    mgr = SecurityManager(policy_path=policy_path)
    yield mgr
    # аккуратно закрываем файл, чтобы Windows/CI не ругался
    try:
        mgr._audit_fp.close()
    except Exception:
        pass


def test_policy_is_loaded_and_applied(tmp_path):
    policy_path, policy = write_policy(
        tmp_path,
        window_seconds=30,
        max_fail_ratio=0.25,
        min_events_in_window=3,
        consecutive_fail_threshold=2,
        lockout_seconds=7,
        cooldown_seconds=11,
        action_during_lockout="reject",
        weights={"invalid_signature": 2.0},
    )
    mgr = SecurityManager(policy_path=policy_path)
    try:
        assert mgr.window_seconds == 30.0
        assert mgr.max_fail_ratio == 0.25
        assert mgr.min_events_in_window == 3
        assert mgr.consecutive_fail_threshold == 2
        assert mgr.lockout_seconds == 7
        assert mgr.cooldown_seconds == 11
        assert mgr.action_during_lockout == "reject"
        assert mgr.weights["invalid_signature"] == 2.0
        assert mgr.security_log_path.endswith("security.log")
        assert mgr.audit_log_path.endswith("security_audit.jsonl")
    finally:
        try:
            mgr._audit_fp.close()
        except Exception:
            pass


def test_on_packet_before_verify_allows_when_not_locked(sm, tmp_path):
    meta = {"src": "unit-test", "packet_id": 1}
    assert sm.on_packet_before_verify(meta) is True

    audit_path = tmp_path / "logs" / "security_audit.jsonl"
    # В этом коде при allow audit НЕ пишется — фиксируем текущее поведение
    assert read_audit_lines(audit_path) == []


def test_on_packet_before_verify_blocks_and_audits_when_locked(sm, tmp_path, monkeypatch):
    # фиксируем "сейчас"
    t = 1000.0
    monkeypatch.setattr("ground.security.security_manager.time.time", lambda: t)

    sm._lockout_until = t + 10  # lockout активен

    meta = {"src": "unit-test", "packet_id": 2}
    assert sm.on_packet_before_verify(meta) is False

    audit_path = tmp_path / "logs" / "security_audit.jsonl"
    lines = read_audit_lines(audit_path)
    assert len(lines) == 1
    rec = lines[0]
    assert rec["event"] == "lockout_drop"
    assert rec["ok"] is False
    assert rec["reason"] == "lockout_active"
    assert rec["meta"] == meta


def test_consecutive_fails_trigger_lockout(tmp_path, monkeypatch):
    policy_path, _ = write_policy(
        tmp_path,
        consecutive_fail_threshold=3,
        min_events_in_window=999,      # чтобы ratio-ветка не мешала
        max_fail_ratio=0.0001,         # неважно
        lockout_seconds=50,
    )
    mgr = SecurityManager(policy_path=policy_path)
    try:
        t = 1000.0
        monkeypatch.setattr(
            "ground.security.security_manager.time.time",
            lambda: t
        )

        meta = {"src": "unit-test"}
        mgr.on_verification_result(False, "invalid_signature", meta)
        mgr.on_verification_result(False, "invalid_signature", meta)
        assert mgr.is_locked() is False  # ещё не достигли 3

        mgr.on_verification_result(False, "invalid_signature", meta)
        assert mgr.is_locked() is True   # lockout включён

        # после lockout consecutive сбрасывается
        assert mgr._consecutive_fail == 0
    finally:
        try:
            mgr._audit_fp.close()
        except Exception:
            pass


def test_weighted_fail_ratio_can_trigger_lockout(tmp_path, monkeypatch):
    # Настраиваем так, чтобы ratio сработал,
    # и чтобы consecutive НЕ сработал.
    policy_path, _ = write_policy(
        tmp_path,
        consecutive_fail_threshold=999,
        min_events_in_window=4,
        max_fail_ratio=0.20,     # важно: из-за текущей формулы порога lockout будет при ratio >= 0.4
        lockout_seconds=60,
        weights={"invalid_signature": 1.0},
    )
    mgr = SecurityManager(policy_path=policy_path)
    try:
        t = 2000.0
        monkeypatch.setattr("ground.security.security_manager.time.time", lambda: t)

        meta = {"src": "unit-test"}

        # 4 события: 2 fail + 2 ok => fail_w=2, total_w=4 => ratio=0.5
        mgr.on_verification_result(False, "invalid_signature", meta)
        mgr.on_verification_result(True, "ok", meta)
        mgr.on_verification_result(False, "invalid_signature", meta)
        mgr.on_verification_result(True, "ok", meta)

        assert mgr.is_locked() is True
    finally:
        try:
            mgr._audit_fp.close()
        except Exception:
            pass


def test_trim_window_removes_old_events(tmp_path, monkeypatch):
    policy_path, _ = write_policy(
        tmp_path,
        window_seconds=10,
        consecutive_fail_threshold=999,
        min_events_in_window=999,
    )
    mgr = SecurityManager(policy_path=policy_path)
    try:
        meta = {"src": "unit-test"}

        # время 0..2: добавим несколько событий
        t = 0.0
        monkeypatch.setattr("ground.security.security_manager.time.time", lambda: t)
        mgr.on_verification_result(True, "ok", meta)

        t = 2.0
        monkeypatch.setattr("ground.security.security_manager.time.time", lambda: t)
        mgr.on_verification_result(True, "ok", meta)

        assert len(mgr._events) == 2

        # прыгаем далеко за окно
        t = 25.0
        monkeypatch.setattr("ground.security.security_manager.time.time", lambda: t)
        mgr.on_verification_result(True, "ok", meta)

        # после trim в окне должны остаться только "свежие" события
        # (точное число зависит от border, но старые обязаны уйти)
        assert all(ev.ts >= (t - mgr.window_seconds) for ev in mgr._events)
    finally:
        try:
            mgr._audit_fp.close()
        except Exception:
            pass


def test_safe_meta_strips_sensitive_fields():
    from ground.security.security_manager import SecurityManager as SM
    meta = {"hmac": "aaa", "secret": "bbb", "key": "ccc", "packet_id": 7, "src": "x"}
    safe = SM._safe_meta(meta)

    assert safe["hmac"] == "***"
    assert safe["secret"] == "***"
    assert safe["key"] == "***"
    assert safe["packet_id"] == 7
    assert safe["src"] == "x"
