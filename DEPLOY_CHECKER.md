# Deploy Checker v0.1

Checks every live Team 2 deploy and reports UP/DOWN, HTTP status and response time.

    python3 deploy_checker.py            # table output, exit 1 if anything is down
    python3 deploy_checker.py --json     # machine-readable
    python3 deploy_checker.py --targets my_targets.json   # {"Name": "https://url"}
    python3 -m pytest test_deploy_checker.py

No dependencies (stdlib only). Designed to run from the hourly watch / cron; non-zero exit = alert.
