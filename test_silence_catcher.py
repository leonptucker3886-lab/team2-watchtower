import json
from datetime import datetime, timezone
from pathlib import Path
from silence_catcher import find_silent, DEFAULT_TEAM, parse_ts
SAMPLE = Path(__file__).resolve().parent / "sample_messages.json"
def test_flags_only_silent():
    msgs = json.loads(SAMPLE.read_text())
    s = find_silent(msgs, DEFAULT_TEAM, 60, parse_ts("2026-10-31T07:15:00Z"))
    assert [x[0] for x in s] == ["Cpl Jude Johnson"]
def test_missing_member_flagged():
    s = find_silent([], DEFAULT_TEAM, 60, datetime.now(timezone.utc))
    assert len(s) == 3
