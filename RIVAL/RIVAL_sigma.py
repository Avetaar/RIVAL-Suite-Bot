import httpx
import RIVAL_config as CFG
import RIVAL_proxies as PX
API_BASE = CFG.SIGMA_BASE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
_MODELS = {
    "sigma-gpt54n": ("chat", "gpt-5.4-nano", "GPT-5.4 Nano"),
    "sigma-gpt54m": ("chat", "gpt-5.4-mini", "GPT-5.4 Mini"),
    "sigma-gpt52":  ("chat", "gpt-5.2", "GPT-5.2"),
    "sigma-gpt51":  ("chat", "gpt-5.1", "GPT-5.1"),
    "sigma-gpt4o":  ("chat", "chatgpt-4o-latest", "ChatGPT 4o"),
}
def models_by_type(t):
    return [m for m, (k, _, _) in _MODELS.items() if k == t]
def display_label(mid):
    return _MODELS.get(mid, (None, None, mid))[2]
def _raw(mid):
    return _MODELS.get(mid, (None, None, mid))[1]
def is_exhausted(ex):
    s = str(ex).lower()
    return any(t in s for t in ("429", "460", "403", "rate", "busy", "connect"))
async def chat(mid, msgs, proxy=None, system=None, tg_id: int = None):
    raw = _raw(mid)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.extend(msgs or [{"role": "user", "content": "hi"}])
    pxs = [None] + ([proxy] if proxy else [])
    if not proxy and PX.get_proxy():
        pxs.append(PX.get_proxy())
    last = None
    for px in pxs:
        try:
            async with httpx.AsyncClient(proxy=px, timeout=CFG.SIGMA_TIMEOUT,
                                         verify=False) as c:
                r = await c.post(
                    f"{API_BASE}/api/openai/v1/chat/completions",
                    json={"messages": messages, "model": raw,
                          "temperature": 0.7, "stream": False},
                    headers={"User-Agent": UA, "Content-Type": "application/json",
                             "Origin": API_BASE, "Referer": f"{API_BASE}/",
                             "Accept": "application/json, text/event-stream"})
                if r.status_code == 200:
                    j = r.json()
                    out = (j.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                    out = out.strip()
                    if not out:
                        raise RuntimeError("sigma chat: رد فاضٍ")
                    return out
                raise RuntimeError(f"sigma chat HTTP {r.status_code}: {r.text[:200]}")
        except RuntimeError:
            raise
        except Exception as ex:
            last = ex
            continue
    raise RuntimeError(f"sigma: تعذر الوصول ({last})")
