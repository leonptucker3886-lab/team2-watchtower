import json
from datetime import datetime, timezone
from silence_catcher import find_silent, DEFAULT_TEAM, parse_ts
def test_flags_only_silent():
    msgs = json.load(open("sample_messages.json"))
    s = find_silent(msgs, DEFAULT_TEAM, 60, parse_ts("2026-10-31T07:15:00Z"))
    assert [x[0] for x in s] == ["Cpl Jude Johnson"]
def test_missing_member_flagged():
    s = find_silent([], DEFAULT_TEAM, 60, datetime.now(timezone.utc))
    assert len(s) == 3
