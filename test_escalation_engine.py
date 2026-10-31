from datetime import datetime, timezone, timedelta
import escalation_engine as ee

T = {"a": "Alpha", "b": "Bravo"}
NOW = datetime(2026, 10, 31, 14, 0, tzinfo=timezone.utc)


def msgs(**mins):
    return [{"senderId": k, "ts": (NOW - timedelta(minutes=v)).isoformat()} for k, v in mins.items()]


def test_ping_then_escalate_then_clear():
    s = {"open_pings": {}, "actions": []}
    a1 = ee.run(msgs(a=5, b=90), T, 60, NOW, s, False, dry=True)
    assert [(x["action"], x["member"]) for x in a1] == [("ping", "Bravo")]
    a2 = ee.run(msgs(a=5, b=120), T, 60, NOW, s, False, dry=True)
    assert [(x["action"], x["member"]) for x in a2] == [("escalate", "Bravo")]
    assert ee.run(msgs(a=5, b=150), T, 60, NOW, s, False, dry=True) == []
    a4 = ee.run(msgs(a=5, b=1), T, 60, NOW, s, False, dry=True)
    assert [(x["action"], x["member"]) for x in a4] == [("cleared", "Bravo")]
    assert len(s["actions"]) == 3
