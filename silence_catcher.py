#!/usr/bin/env python3
"""Silence Catcher v0.1 - flags Team 2 members silent for more than N minutes.

Reads recent topic messages (from the Zenzap API or a JSON file), finds each
watched member's last post, and prints/posts an alert for anyone silent too long.
Standard library only.
"""
import argparse, json, os, sys, urllib.request
from datetime import datetime, timezone

DEFAULT_TEAM = {
    "b@6cd655cb-f20b-4260-9ff2-bb65f7e4e340": "Maj Pizzapan",
    "b@604533f3-05c9-4ffa-9066-8393a5c2598c": "Cpl Jude Johnson",
    "b@7e07950b-4b31-43a9-be1d-67f9d59b6b13": "Sgt Ghenguis Kuha",
}

def parse_ts(v):
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=timezone.utc)
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

def api(method, url, token, body=None):
    req = urllib.request.Request(url, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")

def load_messages(args):
    if args.input:
        data = json.load(open(args.input))
    else:
        url = f"{args.api_base}/topics/{args.topic}/messages?limit=100&order=desc"
        data = api("GET", url, args.token)
    if isinstance(data, dict):
        data = data.get("messages") or data.get("data") or data.get("items") or []
    return data

def last_seen(messages, team):
    seen = {}
    for m in messages:
        sid = m.get("senderId") or m.get("sender_id") or (m.get("sender") or {}).get("id")
        ts = m.get("createdAt") or m.get("ts") or m.get("timestamp")
        if sid in team and ts is not None:
            t = parse_ts(ts)
            if sid not in seen or t > seen[sid]:
                seen[sid] = t
    return seen

def find_silent(messages, team, threshold_min, now):
    seen = last_seen(messages, team)
    out = []
    for sid, name in team.items():
        t = seen.get(sid)
        mins = None if t is None else int((now - t).total_seconds() // 60)
        if t is None or mins > threshold_min:
            out.append((name, t, mins))
    return out

def format_alert(silent, threshold_min):
    if not silent:
        return None
    lines = [f"SILENCE ALERT: no post in over {threshold_min} min:"]
    for name, t, mins in silent:
        lines.append(f"- {name}: " + ("no post in recent window" if t is None
                     else f"last posted {t:%H:%M} UTC ({mins} min ago)"))
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="JSON file of messages (offline mode)")
    p.add_argument("--topic", default=os.getenv("ZENZAP_TOPIC_ID"))
    p.add_argument("--api-base", default=os.getenv("ZENZAP_API_BASE", "https://api.zenzap.co/v2"))
    p.add_argument("--token", default=os.getenv("ZENZAP_API_TOKEN"))
    p.add_argument("--threshold", type=int, default=60)
    p.add_argument("--team", help="JSON file mapping profileId -> name")
    p.add_argument("--now", help="ISO time override (testing)")
    p.add_argument("--post", action="store_true", help="post alert to the topic")
    a = p.parse_args()
    team = json.load(open(a.team)) if a.team else DEFAULT_TEAM
    now = parse_ts(a.now) if a.now else datetime.now(timezone.utc)
    if not a.input and not (a.topic and a.token):
        sys.exit("Need --input, or ZENZAP_TOPIC_ID and ZENZAP_API_TOKEN")
    alert = format_alert(find_silent(load_messages(a), team, a.threshold, now), a.threshold)
    print(alert or "All Team 2 members active.")
    if alert and a.post:
        api("POST", f"{a.api_base}/messages", a.token, {"topicId": a.topic, "text": alert})
    return 1 if alert else 0

if __name__ == "__main__":
    sys.exit(main())
