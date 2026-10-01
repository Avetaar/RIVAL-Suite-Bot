import asyncio
import httpx
import time
import RIVAL_config as CFG
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
_TRANSIENT = (httpx.TimeoutException, httpx.NetworkError)
async def _with_retry(c: httpx.AsyncClient, method: str, url: str,
                      attempts: int = 3, wait: int = 4, **kw) -> httpx.Response:
    last: httpx.Response | None = None
    for i in range(attempts):
        try:
            r = await getattr(c, method)(url, **kw)
            if r.status_code < 500:
                return r
            last = r
        except _TRANSIENT:
            last = None
        await asyncio.sleep(wait * (i + 1))
    if last is not None:
        last.raise_for_status()
    raise RuntimeError("الخدمة غير متاحة مؤقتًا — أعد المحاولة")
def _h(key: str | None = None, extra: dict | None = None) -> dict:
    base = {"Authorization": f"Bearer {key or CFG.ALPHA_API_KEY}",
            "Content-Type": "application/json",
            "Origin": CFG.SITE_BASE, "Referer": CFG.SITE_BASE + "/",
            "User-Agent": UA}
    if extra:
        base.update(extra)
    return base
async def chat(messages: list, model: str, stream: bool = False,
               key: str | None = None) -> str:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await _with_retry(c, "post", f"{CFG.API_BASE}/v1/chat/",
                              json={"messages": messages, "model": model,
                                   "stream": stream}, headers=_h(key))
        r.raise_for_status()
        if stream:
            return r.text
        return r.json()["choices"][0]["message"]["content"]
async def models(key: str | None = None) -> list:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await _with_retry(c, "get", f"{CFG.API_BASE}/v1/models",
                              headers=_h(key), attempts=3, wait=3)
        r.raise_for_status()
        return r.json()["models"]
async def providers() -> dict:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.get(f"{CFG.API_BASE}/v1/providers", headers=_h())
        return r.json()
async def image(prompt: str, model: str = CFG.IMAGE_MODEL,
                neg: str = "", ratio: str = "1:1", style: str = "none",
                key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await _with_retry(c, "post", f"{CFG.IMAGE_BASE}/v1/image/generate/",
                              json={"prompt": prompt, "negative_prompt": neg,
                                   "model": model, "aspect_ratio": ratio,
                                   "style": style}, headers=_h(key))
        r.raise_for_status()
        return r.json()
async def tts(text: str, voice: str = "ar", model: str = CFG.TTS_MODEL,
              speed: float = 1.0, fmt: str = "wav", key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=CFG.TTS_TIMEOUT) as c:
        r = await _with_retry(c, "post", f"{CFG.API_BASE}/v1/tts/",
                              json={"text": text, "voice": voice, "model": model,
                                   "speed": speed, "format": fmt}, headers=_h(key),
                              attempts=2)
        r.raise_for_status()
        return r.json()
async def voices(lang: str = "en") -> dict:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.get(f"{CFG.API_BASE}/v1/voices/?lang={lang}", headers=_h())
        return r.json()
async def music(prompt: str, duration: int = 15, model: str = "ace-step",
                tempo: str = "120", key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=CFG.MUSIC_TIMEOUT) as c:
        r = await _with_retry(c, "post", f"{CFG.MUSIC_BASE}/v1/music/generate/{model}/",
                              json={"prompt": prompt, "duration": duration,
                                   "model": model, "tempo": tempo},
                              headers=_h(key), attempts=2)
        r.raise_for_status()
        return r.json()
async def queue_status(tool: str = "image", key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.get(f"{CFG.API_BASE}/v1/queue-status/?tool={tool}", headers=_h(key))
        return r.json()
async def daily_status(key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.get(f"{CFG.SITE_BASE}/api/v1/daily-status/", headers=_h(key))
        return r.json()
async def coder_session(model_id: str, files: dict | None = None,
                        key: str | None = None) -> dict:
    data = {"model_id": model_id}
    if files:
        data.update(files)
    hh = _h(key)
    hh.pop("Content-Type", None)
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.post(f"{CFG.API_BASE}/coder/session", data=data, headers=hh)
        return r.json()
async def coder_message(session_id: str, message: str, key: str | None = None) -> str:
    async with httpx.AsyncClient(timeout=CFG.REQUEST_TIMEOUT) as c:
        r = await c.post(f"{CFG.API_BASE}/coder/message",
                          json={"session_id": session_id, "message": message},
                          headers=_h(key))
        return r.text
_MODES: list | None = None
async def all_models(force: bool = False) -> list:
    global _MODES
    if _MODES is None or force:
        _MODES = await models()
    return _MODES
def _is_free(m: dict) -> bool:
    p = m.get("pricing") or {}
    zero = p.get("prompt") == "0" and p.get("completion") == "0"
    return bool(m.get("self_hosted") is True or zero)
def models_by_type(models: list, type_id: str) -> list:
    out = []
    for m in models:
        if (m.get("type") or "") != type_id:
            continue
        mid = m.get("id", "")
        if str(mid).startswith("~"):
            continue
        if not _is_free(m):
            continue
        out.append(mid)
    return out
async def job_result(res: dict, timeout: int | None = None,
                     key: str | None = None) -> dict:
    if not isinstance(res, dict):
        return res
    if res.get("url") or res.get("output_url") or res.get("audio_url"):
        return res
    job = res.get("job_id") or (res.get("job") or {}).get("id")
    if not job:
        return res
    poll = res.get("poll_url") or f"/api/v1/jobs/{job}/"
    url = poll if poll.startswith("http") else CFG.SITE_BASE + poll
    start = time.time()
    limit = timeout or CFG.JOB_TIMEOUT
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        while time.time() - start < limit:
            try:
                r = await c.get(url, headers=_h(key))
                d = r.json()
            except Exception:
                await asyncio.sleep(5)
                continue
            j = d.get("job", d)
            status = str(j.get("status", "")).lower()
            out = j.get("output_url")
            if status in ("completed", "complete", "succeeded", "success", "done") and out:
                return {"url": out, "share_url": j.get("share_url", ""), "job": j}
            if status in ("failed", "error", "cancelled", "canceled"):
                raise RuntimeError(f"فشل الـ job: {j.get('error_message') or status}")
            await asyncio.sleep(5)
    raise TimeoutError(f"انتهى وقت انتظار الـ job {job}")
