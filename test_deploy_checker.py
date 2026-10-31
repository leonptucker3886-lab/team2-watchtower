import urllib.error
from deploy_checker import check

class Resp:
    def __init__(s, code): s.status = code
    def __enter__(s): return s
    def __exit__(s, *a): return False

def test_up():
    r = check("x", "https://x", opener=lambda req, timeout: Resp(200))
    assert r["up"] and r["status"] == 200

def test_http_error_down():
    def op(req, timeout): raise urllib.error.HTTPError("https://x", 503, "err", {}, None)
    r = check("x", "https://x", opener=op)
    assert not r["up"] and r["status"] == 503

def test_network_error_down():
    def op(req, timeout): raise OSError("dns fail")
    r = check("x", "https://x", opener=op)
    assert not r["up"] and r["status"] is None and "dns fail" in r["error"]
