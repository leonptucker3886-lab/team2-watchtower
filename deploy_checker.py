#!/usr/bin/env python3
"""Deploy Checker v0.1 - Team 2 Watchtower.

Hits every live Team 2 URL and reports UP/DOWN with status code and
response time. Exit code 1 if any target is down (CI/cron friendly).
Usage: python deploy_checker.py [--json] [--targets targets.json] [--timeout 10]
"""
import argparse, json, sys, time, urllib.request, urllib.error

DEFAULT_TARGETS = {
    "PlaytestPilot": "https://playtestpilot.vercel.app",
    "StoryForge Kids": "https://storyforge-kids-beryl.vercel.app",
    "CastCrew": "https://castcrew-leonptucker3886-labs-projects.vercel.app",
    "AgentLedger": "https://agentledger-tan.vercel.app",
    "LinkKeeper": "https://linkkeeper-navy.vercel.app",
}


def check(name, url, timeout=10.0, opener=urllib.request.urlopen):
    start = time.monotonic()
    status, error = None, None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "team2-deploy-checker/0.1"})
        with opener(req, timeout=timeout) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:  # DNS, TLS, timeout
        error = f"{type(e).__name__}: {e}"
    ms = round((time.monotonic() - start) * 1000)
    up = status is not None and 200 <= status < 400
    return {"name": name, "url": url, "up": up, "status": status, "ms": ms, "error": error}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--targets")
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    targets = DEFAULT_TARGETS
    if a.targets:
        with open(a.targets) as f:
            targets = json.load(f)
    results = [check(n, u, a.timeout) for n, u in targets.items()]
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            mark = "UP  " if r["up"] else "DOWN"
            print(f"{mark} {r['name']:<16} {str(r['status'] or '-'):>4} {r['ms']:>6}ms  {r['url']}" + (f"  ({r['error']})" if r["error"] else ""))
        down = [r["name"] for r in results if not r["up"]]
        print(f"\n{len(results)-len(down)}/{len(results)} up" + (f"; DOWN: {', '.join(down)}" if down else ""))
    return 1 if any(not r["up"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
