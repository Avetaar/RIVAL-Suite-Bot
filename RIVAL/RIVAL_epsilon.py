import asyncio
import json
import os
import re
import httpx
import RIVAL_config as CFG
API_BASE = CFG.EPS_API_BASE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
CATALOG = [
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-r1",
    "deepseek/deepseek-v3.2",
]
BLOCKED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "RIVAL_eps_blocked.json")
def load_blocked():
    try:
        with open(BLOCKED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()
def models_by_type(t):
    if t != "chat":
        return []
    bl = load_blocked()
    return [m for m in CATALOG if m not in bl]
def display_label(mid):
    return mid.split("/")[-1]
_CS = {"client": None, "token": None}
_LOCK = asyncio.Lock()
async def _page(client):
    r = await client.get(f"{API_BASE}/ar/chat", follow_redirects=True)
    m = (re.search(r'name="csrf-token"\s+content="([^"]+)"', r.text) or
         re.search(r'content="([^"]+)"\s+name="csrf-token"', r.text))
    return m.group(1) if m else None
async def _new_session(proxy=None):
    c = httpx.AsyncClient(cookies={}, proxy=proxy, timeout=CFG.EPS_CHAT_TIMEOUT,
                         verify=False, headers={"User-Agent": UA})
    tok = await _page(c)
    if not tok:
        raise RuntimeError("eps: ماكو رمز جلسة في الصفحة")
    return c, tok
async def _ensure_session(proxy=None, force=False):
    async with _LOCK:
        if force and _CS["client"] and not _CS["client"].is_closed:
            await _CS["client"].aclose()
        if _CS["client"] is None or _CS["client"].is_closed:
            _CS["client"], _CS["token"] = await _new_session(proxy)
        return _CS["client"], _CS["token"]
def _iter_sse(text):
    out = ""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        try:
            d = json.loads(line[5:].strip())
        except Exception:
            continue
        if d.get("content"):
            out += d["content"]
        ch = (d.get("choices") or [{}])[0]
        out += (ch.get("delta") or {}).get("content") or ""
        if d.get("finishReason") == "stop" or d.get("finish_reason") == "stop":
            break
    return out.strip()
async def chat(messages, model, proxy=None):
    for _ in range(2):
        client, tok = await _ensure_session(proxy, force=_CS["client"] is not None and proxy)
        hdr = {"Content-Type": "application/json", "X-CSRF-TOKEN": tok,
               "Accept": "text/event-stream", "Cache-Control": "no-cache",
               "Origin": API_BASE, "Referer": f"{API_BASE}/ar/chat",
               "User-Agent": UA}
        r = await client.post(f"{API_BASE}/api/chat",
                              json={"model": model, "messages": messages},
                              headers=hdr)
        if r.status_code in (401, 403, 419):
            _CS["client"], _CS["token"] = None, None
            await _ensure_session(proxy, force=True)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"eps chat HTTP {r.status_code}: {r.text[:200]}")
        out = _iter_sse(r.text)
        if not out:
            raise RuntimeError("eps: رد فاضٍ")
        return out
    raise RuntimeError("eps: فشل بعد تجديد الجلسة")
def is_exhausted(ex):
    s = str(ex).lower()
    return ("429" in s or "401" in s or "403" in s or "419" in s
            or "unauthorized" in s or "forbidden" in s)
