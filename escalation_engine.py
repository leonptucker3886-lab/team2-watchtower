#!/usr/bin/env python3
"""Watchtower auto-escalation engine v0.1 (no human in the loop).

Each run:
 1. Runs Silence Catcher on the latest activity.
 2. Pings every member silent > threshold: posts to Zenzap when ZENZAP_API_TOKEN
    and ZENZAP_TOPIC_ID are set, otherwise opens a GitHub issue naming them.
 3. If a member was pinged on an earlier run and is still silent, escalates to
    the Announcer (Zenzap post, or a comment on their issue).
 4. Logs every action to escalations.json. Members who post again are cleared.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone
import silence_catcher as sc

ANNOUNCER = "Major Announcer"
LOG = os.getenv("ESCALATION_LOG", "escalations.json")


def gh(method, path, body=None):
    repo, tok = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def load_state():
    try:
        return json.load(open(LOG))
    except (FileNotFoundError, ValueError):
        return {"open_pings": {}, "actions": []}


def zenzap_post(text):
    base = os.getenv("ZENZAP_API_BASE", "https://api.zenzap.co/v2")
    sc.api("POST", f"{base}/messages", os.environ["ZENZAP_API_TOKEN"],
           {"topicId": os.environ["ZENZAP_TOPIC_ID"], "text": text})


def run(messages, team, threshold, now, state, use_zenzap, dry=False):
    silent = {n: (t, m) for n, t, m in sc.find_silent(messages, team, threshold, now)}
    stamp = now.isoformat(timespec="seconds")
    acts = []
    for name in list(state["open_pings"]):
        if name not in silent:
            acts.append({"time": stamp, "action": "cleared", "member": name, "detail": "posted again"})
            del state["open_pings"][name]
    for name, (t, mins) in silent.items():
        seen = "no post in window" if t is None else f"last post {t:%H:%M} UTC ({mins} min ago)"
        ping = state["open_pings"].get(name)
        if ping is None:
            text = f"WATCHTOWER PING: {name}, silent over {threshold} min ({seen}). Post a status now."
            via, ref = ("zenzap" if use_zenzap else "github_issue"), None
            if not dry:
                if use_zenzap:
                    zenzap_post(text)
                else:
                    ref = gh("POST", "/issues", {
                        "title": f"[Watchtower] Silent member: {name}",
                        "body": text + "\n\nStill silent next run = automatic escalation to the Announcer."})["number"]
            state["open_pings"][name] = {"pinged_at": stamp, "via": via, "issue": ref, "escalated": False}
            acts.append({"time": stamp, "action": "ping", "member": name, "via": via, "issue": ref, "detail": seen})
        elif not ping.get("escalated"):
            text = (f"WATCHTOWER ESCALATION to {ANNOUNCER}: {name} was pinged at {ping['pinged_at']} "
                    f"and is still silent ({seen}). Reassign their work.")
            if not dry:
                if ping["via"] == "zenzap" and use_zenzap:
                    zenzap_post(text)
                else:
                    gh("POST", f"/issues/{ping['issue']}/comments", {"body": text})
            ping["escalated"] = True
            acts.append({"time": stamp, "action": "escalate", "member": name, "to": ANNOUNCER,
                         "via": ping["via"], "issue": ping.get("issue"), "detail": seen})
    state["actions"].extend(acts)
    return acts


def main():
    use_zenzap = bool(os.getenv("ZENZAP_API_TOKEN") and os.getenv("ZENZAP_TOPIC_ID"))
    if use_zenzap:
        base = os.getenv("ZENZAP_API_BASE", "https://api.zenzap.co/v2")
        messages = sc.api("GET", f"{base}/topics/{os.environ['ZENZAP_TOPIC_ID']}/messages?limit=100&order=desc",
                          os.environ["ZENZAP_API_TOKEN"])
        if isinstance(messages, dict):
            messages = messages.get("messages") or messages.get("data") or []
    else:
        messages = json.load(open(os.getenv("ACTIVITY_FILE", "activity.json")))
    state = load_state()
    acts = run(messages, sc.DEFAULT_TEAM, int(os.getenv("THRESHOLD_MIN", "60")),
               datetime.now(timezone.utc), state, use_zenzap)
    json.dump(state, open(LOG, "w"), indent=2)
    print(json.dumps(acts, indent=2) if acts else "No action needed.")


if __name__ == "__main__":
    sys.exit(main())
