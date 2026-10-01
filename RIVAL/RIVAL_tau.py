import asyncio
import re
import time
import httpx
import RIVAL_config as CFG
import RIVAL_proxies as PX
BASE = CFG.TAU_BASE
MAIL = CFG.TAU_MAIL_BASE
UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36")
_MODELS = {
    "tau-claude-sonnet5": ("chat", "claude-sonnet-5", "Claude Sonnet 5"),
    "tau-claude-48":      ("chat", "claude-opus-4-8", "Claude Opus 4.8"),
    "tau-grok-43":        ("chat", "grok-4.3", "Grok 4.3"),
    "tau-grok-45":        ("chat", "grok-4.5", "Grok 4.5"),
}
_TK = {"token": None, "chat": None, "created_at": 0.0}
def models_by_type(t):
    return [m for m, (_, _, _) in _MODELS.items() if _MODELS[m][0] == t]
def display_label(mid):
    return _MODELS.get(mid, (None, None, mid))[2]
def _raw(mid):
    return _MODELS.get(mid, (None, None, mid))[1]
def _ai_name(mid):
    return "claude" if _raw(mid).startswith("claude") else "grok"
def is_exhausted(ex):
    s = str(ex).lower()
    return any(t in s for t in ("401", "403", "token", "expired", "otp",
                                 "inbox", "verify", "429", "tempmail"))
async def _mail_new(c: httpx.AsyncClient) -> str:
    r = await c.get(f"{MAIL}/api/v1/new",
                    headers={"User-Agent": UA, "Accept": "application/json"})
    if r.status_code != 200:
        raise RuntimeError(f"tau mail new HTTP {r.status_code}")
    d = r.json()
    email = d.get("email") or (d.get("data") or {}).get("email")
    if not email:
        raise RuntimeError(f"tau mail new: ماكو email ({str(d)[:80]})")
    return email
async def _mail_otp(c: httpx.AsyncClient, email: str,
                    wait_s: int = CFG.TAU_MAIL_WAIT) -> str:
    deadline = time.time() + wait_s
    seen = set()
    while time.time() < deadline:
        r = await c.get(f"{MAIL}/api/v1/inbox?email={email}",
                        headers={"User-Agent": UA, "Accept": "application/json"})
        if r.status_code == 200:
            body = r.json()
            lst = (body if isinstance(body, list) else
                   (body.get("messages") or body.get("data") or []))
            if isinstance(lst, list):
                for m in lst:
                    mid = m.get("id") or m.get("msg_id")
                    txt = (m.get("text") or m.get("body") or "")
                    if mid and mid not in seen:
                        seen.add(mid)
                        if not txt:
                            r2 = await c.get(
                                f"{MAIL}/api/v1/message?email={email}&msg_id={mid}",
                                headers={"User-Agent": UA,
                                         "Accept": "application/json"})
                            b2 = r2.json()
                            txt = (b2.get("text") or b2.get("body") or
                                   (b2.get("data") or {}).get("text") or "")
                    mm = re.search(r"\b(\d{6})\b", txt or "")
                    if mm:
                        return mm.group(1)
        await asyncio.sleep(5)
    raise RuntimeError("tau otp: ما وصل الكود (مهلة الوصل انتهت)")
async def _make_session(c: httpx.AsyncClient):
    email = await _mail_new(c)
    r = await c.post(f"{BASE}/api/v1/auth/email/send-otp",
                     json={"email": email, "ref_uuid": None, "utm": ""},
                     headers={"User-Agent": UA})
    if r.status_code != 200 or not r.json().get("success"):
        raise RuntimeError(f"tau otp send HTTP {r.status_code}: {r.text[:120]}")
    otp = await _mail_otp(c, email)
    r = await c.post(f"{BASE}/api/v1/auth/email/verify-otp",
                     json={"email": email, "otp_code": otp,
                           "ref_uuid": None, "utm": ""},
                     headers={"User-Agent": UA})
    if r.status_code != 200 or not r.json().get("success"):
        raise RuntimeError(f"tau verify HTTP {r.status_code}: {r.text[:120]}")
    token = r.json().get("token")
    if not token:
        raise RuntimeError("tau verify: ماكو token")
    r = await c.post(f"{BASE}/api/v1/chats",
                     json={"title": "R", "scope": "text"},
                     headers={"Authorization": f"Bearer {token}",
                              "User-Agent": UA})
    if r.status_code != 201:
        raise RuntimeError(f"tau chat create HTTP {r.status_code}")
    chat = r.json().get("uuid")
    if not chat:
        raise RuntimeError("tau chat create: ماكو uuid")
    _TK["token"] = token
    _TK["chat"] = chat
    _TK["created_at"] = time.time()
async def _ensure(c: httpx.AsyncClient, force: bool = False):
    if force or not _TK.get("token"):
        await _make_session(c)
    return _TK["token"], _TK["chat"]
async def chat(mid, msgs, proxy=None, system=None, tg_id: int = None):
    raw = _raw(mid)
    ai_name = _ai_name(mid)
    prompt = ""
    for m in reversed(msgs or []):
        if m.get("role") == "user":
            prompt = m.get("content", "")
            break
    if not prompt:
        prompt = str(msgs)
    pxs = [None] + ([proxy] if proxy else [])
    if not proxy and PX.get_proxy():
        pxs.append(PX.get_proxy())
    last = None
    for i, px in enumerate(pxs):
        try:
            force = i == 0 and not _TK.get("token")
            async with httpx.AsyncClient(proxy=px, timeout=CFG.TAU_TIMEOUT,
                                         verify=False) as c:
                token, chat = await _ensure(c, force=force)
                objects = []
                if system:
                    objects.append({"object_type": "text", "object_url": None,
                                    "object_text": system, "model_type": raw})
                objects.append({"object_type": "text", "object_url": None,
                                "object_text": prompt, "model_type": raw})
                h = {"Authorization": f"Bearer {token}", "User-Agent": UA,
                     "Content-Type": "application/json"}
                r = await c.post(f"{BASE}/api/v1/chats/{chat}/messages"
                                 f"?ai_name={ai_name}",
                                 json={"objects": objects}, headers=h)
                if r.status_code != 200:
                    raise RuntimeError(
                        f"tau send HTTP {r.status_code}: {r.text[:120]}")
                mid_send = r.json().get("id") or 0
                out = None
                for _ in range(45):
                    await asyncio.sleep(2)
                    g = await c.get(f"{BASE}/api/v1/chats/{chat}/messages"
                                    f"?page_size=20", headers=h)
                    for msg in g.json().get("messages", []):
                        if (msg.get("author_id") == -1 and
                                (msg.get("id") or 0) > mid_send):
                            o = (msg.get("message_object") or [{}])[0]
                            if (o.get("object_type") == "text" and
                                    o.get("completed")):
                                out = o.get("object_text")
                                break
                    if out:
                        break
                if not out:
                    raise RuntimeError("tau chat: رد فاضٍ (مهلة انتظار انتهت)")
                return out
        except Exception as ex:
            last = ex
            if i > 0:
                _TK["token"] = None
            continue
    raise RuntimeError(f"tau: تعذر الوصول ({last})")
