import json
import os
import httpx
import RIVAL_config as CFG
API_BASE = CFG.GAMA_API_BASE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
_MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "RIVAL_gamma_models.json")
def _load_data() -> dict:
    try:
        with open(_MODELS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
def models_by_type(type_id: str) -> list:
    if type_id != "chat":
        return []
    data = _load_data()
    blocked = data.get("blocked", {})
    if isinstance(blocked, list):
        blocked = {m: "" for m in blocked}
    out = []
    for m in data.get("models", []):
        if m in blocked:
            continue
        out.append(m)
    return out
def display_label(full_id: str) -> str:
    return full_id.split("/", 1)[1] if "/" in full_id else full_id
async def chat(key: str, user_id: str, model: str, messages: list,
               proxy: str | None = None) -> str:
    h = {"Authorization": f"Bearer {key}", "x-user-id": str(user_id),
         "Content-Type": "application/json", "Accept": "application/json",
         "User-Agent": UA}
    async with httpx.AsyncClient(proxy=proxy, timeout=CFG.GAMA_CHAT_TIMEOUT,
                                 verify=False) as c:
        r = await c.post(f"{API_BASE}/v1/chat/completions/",
                         json={"messages": messages, "model": model,
                               "stream": False}, headers=h)
    if r.status_code != 200:
        raise RuntimeError(f"gama chat HTTP {r.status_code}: {r.text[:200]}")
    j = r.json()
    out = (j.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    out = out.strip()
    if not out:
        raise RuntimeError("gama chat: رد فاضٍ")
    return out
async def signup(email: str, password: str, proxy: str | None = None) -> dict:
    h = {"Content-Type": "application/json", "User-Agent": UA}
    async with httpx.AsyncClient(proxy=proxy, timeout=40, verify=False) as c:
        r = await c.post(f"{API_BASE}/v1/auth/signup",
                         json={"email": email, "password": password}, headers=h)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"gama signup HTTP {r.status_code}: {r.text[:120]}")
    d = r.json()
    key = d.get("accessToken")
    uid = (d.get("user") or {}).get("id")
    if not key or not uid:
        raise RuntimeError(f"gama signup: مفقود token/user: {str(d)[:120]}")
    return {"key": key, "user_id": uid, "email": email}
def is_exhausted(ex: Exception) -> bool:
    s = str(ex).lower()
    return ("401" in s or "403" in s or "unauthorized" in s
            or "insufficient" in s or "429" in s or "rate limit" in s)
