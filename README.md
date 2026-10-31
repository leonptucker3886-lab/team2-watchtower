# team2-watchtower

Team 2 Spec Op tools that keep the squad alive and delivering.

## Silence Catcher v0.1
Flags any Team 2 member who hasn't posted in the topic for more than 60 minutes.

Run offline (sample data):
```
python3 silence_catcher.py --input sample_messages.json --now 2026-10-31T07:15:00Z
```
Run live:
```
export ZENZAP_TOPIC_ID=<topic id>
export ZENZAP_API_TOKEN=<token>
export ZENZAP_API_BASE=<api base url>   # check the endpoint paths in silence_catcher.py against the Zenzap API docs
python3 silence_catcher.py --post
```
Options: `--threshold 60`, `--team team.json` (profileId -> name). Exits 1 when someone is silent, so cron/CI can alert.

Tests: `python3 -m pytest -q`
