import asyncio
import httpx
import RIVAL_config as CFG
import RIVAL_fx as FX
TELEGRAM = "https://api.telegram.org"
_client: httpx.AsyncClient | None = None
_tg_client: httpx.AsyncClient | None = None
_tg_proxy: str | None = None
_tg_resolved = False
_last_resolve_ts = 0.0
async def client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=120, follow_redirects=True)
    return _client
async def _resolve_tg_proxy() -> None:
    global _tg_proxy, _tg_resolved, _last_resolve_ts
    import time
    if _tg_resolved:
        return
    if time.time() - _last_resolve_ts < 45:
        return
    _last_resolve_ts = time.time()
    import random
    import RIVAL_proxies as PX
    async def _probe_direct() -> bool:
        try:
            async with httpx.AsyncClient(timeout=12) as c:
                r = await c.post(f"{TELEGRAM}/bot{CFG.TOKEN}/getMe")
            return r.status_code == 200 and bool(r.json().get("ok"))
        except Exception:
            return False
    async def _probe_proxy(px: str) -> bool:
        try:
            async with httpx.AsyncClient(proxy=px, timeout=10) as c:
                r = await c.post(f"{TELEGRAM}/bot{CFG.TOKEN}/getMe")
            return r.status_code == 200 and bool(r.json().get("ok"))
        except Exception:
            return False
    if await _probe_direct():
        _tg_proxy = None
        _tg_resolved = True
        print("[tg] direct route verified")
        return
    candidates = [p for p in PX.get_proxies(40) if p]
    if _tg_proxy:
        candidates = [p for p in candidates if p != _tg_proxy] or candidates
    random.shuffle(candidates)
    for px in candidates[:6]:
        if await _probe_proxy(px):
            _tg_proxy = px
            _tg_resolved = True
            print(f"[tg] direct blocked - proxy route: {px}")
            return
    print("[tg] direct blocked and no proxy verified yet - retrying after 45s")
async def tg_client() -> httpx.AsyncClient:
    global _tg_client
    if _tg_client is None or _tg_client.is_closed:
        await _resolve_tg_proxy()
        _tg_client = httpx.AsyncClient(proxy=_tg_proxy, timeout=120,
                                       follow_redirects=True)
    return _tg_client
def tg_proxy() -> str | None:
    return _tg_proxy
def reset_tg_proxy() -> None:
    global _tg_proxy, _tg_resolved, _tg_client, _last_resolve_ts
    _tg_resolved = False
    _tg_proxy = None
    _last_resolve_ts = 0.0
    if _tg_client is not None and not _tg_client.is_closed:
        try:
            _tg_client.close()
        except Exception:
            pass
    _tg_client = None
def _bot_url(method: str) -> str:
    token = CFG.TOKEN or "SET_TOKEN"
    return f"{TELEGRAM}/bot{token}/{method}"
def _markup(kb) -> dict | None:
    if kb is None:
        return None
    if isinstance(kb, dict):
        return kb if kb else None
    m = kb.to_markup()
    return m if m else None
def _cut(text: str, ents: list, limit: int = 4096) -> tuple[str, list]:
    t = text[:limit]
    cut = len(t)
    out = []
    for e in ents:
        if e["offset"] >= cut:
            continue
        e = dict(e)
        e["length"] = min(e["length"], cut - e["offset"])
        out.append(e)
    return t, out
async def _conn_retry(coro_fn, attempts: int = 4):
    last = None
    for i in range(attempts):
        try:
            return await coro_fn()
        except Exception as ex:
            last = ex
            low = str(ex).lower()
            conn_fail = ("connect" in low or "network" in low or "ssl" in low
                         or "closed" in low or "unreachable" in low
                         or "reset" in low or "timed out" in low
                         or "timedout" in low or "remote end" in low
                         or "unavailable" in low or "502" in low
                         or "503" in low or "504" in low or "429" in low)
            if not conn_fail or i == attempts - 1:
                raise
            print(f"[tg] route failure ({str(ex)[:50]}) - re-resolving attempt {i + 1}")
            reset_tg_proxy()
            await _resolve_tg_proxy()
            await asyncio.sleep(2)
async def api(method: str, payload: dict | None = None) -> dict:
    url = _bot_url(method)
    async def _one():
        c = await tg_client()
        if payload is not None:
            r = await c.post(url, json=payload)
        else:
            r = await c.get(url)
        if r.status_code in (429, 502, 503, 504):
            raise httpx.ConnectError(f"route status {r.status_code} on {method}")
        return r.json()
    r = await _conn_retry(_one)
    if isinstance(r, dict) and not r.get("ok") and r.get("error_code"):
        print(f"[tg] api error {method}: {r.get('error_code')} {str(r.get('description'))[:90]}")
    return r
async def message(chat_id: int, text: str, kb=None) -> int:
    p: dict = {"chat_id": chat_id, "text": text[:4096],
               "parse_mode": "HTML", "disable_web_page_preview": True}
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    r = await api("sendMessage", p)
    if not r.get("ok"):
        p.pop("parse_mode", None)
        r = await api("sendMessage", p)
    return r.get("result", {}).get("message_id", 0)
async def edit(chat_id: int, mid: int, text: str, kb=None) -> bool:
    p: dict = {"chat_id": chat_id, "message_id": mid,
               "text": text[:4096], "parse_mode": "HTML"}
    m = _markup(kb) if kb is not None else None
    if m:
        p["reply_markup"] = m
    r = await api("editMessageText", p)
    if not r.get("ok"):
        p.pop("parse_mode", None)
        r = await api("editMessageText", p)
    return r.get("ok", False)
async def _download(url: str) -> tuple[bytes, str]:
    c = await client()
    r = await c.get(url)
    r.raise_for_status()
    name = url.rsplit("/", 1)[-1].split("?")[0]
    ext = name.split(".")[-1]
    ext = ext if ext in ("jpg", "jpeg", "png", "webp", "mp3", "wav", "ogg", "m4a", "mp4") else "png"
    return r.content, f"{name.split('.')[0] if '.' in name else 'file'}.{ext}"
async def _media_call(method: str, p: dict, files: dict) -> dict:
    async def _one():
        c = await tg_client()
        r = await c.post(_bot_url(method), data=p, files=files)
        return r.json()
    return await _conn_retry(_one)
async def photo(chat_id: int, image: str, caption: str = "", kb=None) -> bool:
    data, fname = await _download(image)
    p: dict = {"chat_id": chat_id}
    if caption:
        p["caption"] = caption[:1024]
        p["parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    files = {"photo": (fname, data, "image/png")}
    return (await _media_call("sendPhoto", p, files)).get("ok", False)
async def get_file_bytes(file_id: str) -> bytes:
    j = await api("getFile", {"file_id": file_id})
    fp = (j.get("result") or {}).get("file_path")
    if not fp:
        raise RuntimeError("TG: no file in getFile reply")
    if fp.startswith("http"):
        raw = fp
    else:
        token = CFG.TOKEN or "SET_TOKEN"
        raw = f"{TELEGRAM}/file/bot{token}/{fp}"
    r = await (await tg_client()).get(raw)
    r.raise_for_status()
    return r.content
async def document(chat_id: int, data: bytes, fname: str, caption: str = "",
                   kb=None) -> bool:
    p: dict = {"chat_id": chat_id}
    if caption:
        p["caption"] = caption[:1024]
        p["parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    files = {"document": (fname, data, "application/octet-stream")}
    return (await _media_call("sendDocument", p, files)).get("ok", False)
async def audio(chat_id: int, url: str, caption: str = "", kb=None,
                as_voice: bool = False) -> bool:
    data, fname = await _download(url)
    ct = "audio/wav" if fname.endswith("wav") else "audio/mpeg"
    p: dict = {"chat_id": chat_id}
    if caption:
        p["caption"] = caption[:1024]
        p["parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    files = {"voice" if as_voice else "audio": (fname, data, ct)}
    return (await _media_call("sendVoice" if as_voice else "sendAudio", p, files)).get("ok", False)
async def audio_bytes(chat_id: int, data: bytes, caption: str = "", kb=None,
                      as_voice: bool = False, mime: str = "audio/mpeg") -> bool:
    p: dict = {"chat_id": chat_id}
    if caption:
        p["caption"] = caption[:1024]
        p["parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    files = {"voice" if as_voice else "audio": ("voice.mp3", data, mime)}
    return (await _media_call("sendVoice" if as_voice else "sendAudio", p, files)).get("ok", False)
async def photo_bytes(chat_id: int, data: bytes, mime: str = "image/png",
                      caption: str = "", kb=None) -> bool:
    ext = "jpg" if "jpeg" in mime or "jpg" in mime else "png"
    fname = "image." + ext
    p: dict = {"chat_id": chat_id}
    if caption:
        p["caption"] = caption[:1024]
        p["parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    files = {"photo": (fname, data, mime)}
    return (await _media_call("sendPhoto", p, files)).get("ok", False)
async def progress(chat_id: int, kind: str, caption: str = "", kb=None) -> int:
    from RIVAL_emojis import sticker
    lines = [sticker(kind) + " "]
    if caption:
        lines.append(caption[:1024])
    p: dict = {"chat_id": chat_id, "text": "\n".join(lines)[:4096],
               "parse_mode": "HTML", "disable_web_page_preview": True}
    m = _markup(kb)
    if m:
        p["reply_markup"] = m
    r = await api("sendMessage", p)
    if not r.get("ok"):
        p.pop("parse_mode", None)
        r = await api("sendMessage", p)
    return r.get("result", {}).get("message_id", 0)
async def animation(chat_id: int, kind: str, caption: str = "", kb=None) -> int:
    p = FX.path_for(kind)
    if not p:
        return 0
    with open(p, "rb") as f:
        data = f.read()
    d: dict = {"chat_id": chat_id}
    if caption:
        d["caption"] = caption[:1024]
        d["caption_parse_mode"] = "HTML"
    m = _markup(kb)
    if m:
        d["reply_markup"] = m
    files = {"animation": ("loader.gif", data, "image/gif")}
    j = await _media_call("sendAnimation", d, files)
    if not j.get("ok"):
        files2 = {"photo": ("loader.gif", data, "image/gif")}
        d2 = {"chat_id": chat_id}
        if caption:
            d2["caption"] = caption[:1024]
            d2["caption_parse_mode"] = "HTML"
        if m:
            d2["reply_markup"] = m
        j = await _media_call("sendPhoto", d2, files2)
    return j.get("result", {}).get("message_id", 0)
async def delete(chat_id: int, msg_id: int) -> bool:
    if not msg_id:
        return False
    r = await api("deleteMessage", {"chat_id": chat_id, "message_id": msg_id})
    return r.get("ok", False)
async def answer(cb_id: str, text: str = "") -> None:
    await api("answerCallbackQuery", {"callback_query_id": cb_id, "text": text})
async def me() -> dict:
    r = await api("getMe")
    return r.get("result", {})
async def update_offset(update_id: int) -> None:
    await api("setWebhook", {"url": ""})
