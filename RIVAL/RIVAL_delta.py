import base64
import json
import os
import time
import httpx
import RIVAL_config as CFG
API_BASE = CFG.DELTA_API_BASE
UA = ("Mozilla/5.0 (Linux; Android 13; RivalDevice) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
_UA_HDR = {"User-Agent": UA, "Accept-Encoding": "gzip"}
import os
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "RIVAL_delta_models.json")
def load_models() -> list:
    try:
        with open(_PATH, encoding="utf-8") as f:
            return list(json.load(f).get("models", []))
    except Exception:
        return []
def load_blocked() -> set:
    try:
        with open(_PATH, encoding="utf-8") as f:
            return set(json.load(f).get("blocked", {}).keys())
    except Exception:
        return set()
def models_by_type(t: str) -> list:
    if t != "chat":
        return []
    bl = load_blocked()
    return [m for m in load_models() if m not in bl]
def display_label(mid: str) -> str:
    return mid
def _token_exp(tok: str) -> float:
    try:
        p = tok.split(".")[1]
        p += "=" * (-len(p) % 4)
        return (json.loads(base64.urlsafe_b64decode(p))["exp"])
    except Exception:
        return time.time() + 3500
async def signup(proxy: str | None = None) -> dict:
    async with httpx.AsyncClient(proxy=proxy, timeout=40, verify=False) as c:
        r = await c.post(f"{API_BASE}/signup/", json={},
                         headers={"User-Agent": "okhttp/4.12.0"},
                         timeout=40)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"delta signup HTTP {r.status_code}: {r.text[:150]}")
    d = r.json()
    key = d.get("accessToken")
    if not key:
        raise RuntimeError(f"delta signup: لا توكن: {str(d)[:150]}")
    return {"key": key, "user_id": None, "email": None,
            "expiry": _token_exp(key)}
def _auth_header(key: str) -> dict:
    return {**_UA_HDR, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json; charset=UTF-8"}
def _iter_sse(text: str) -> tuple[str, str | None]:
    out, fin = "", None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        d = json.loads(line[5:].strip())
        if d.get("content"):
            out += d["content"]
        if d.get("finishReason"):
            fin = d["finishReason"]
        if fin == "stop":
            break
    return out.strip(), fin
async def chat(key: str, model: str, messages: list,
               proxy: str | None = None) -> str:
    system = ""
    msgs = []
    for m in messages:
        if m.get("role") == "system":
            system = m.get("content", "")
        else:
            msgs.append(m)
    text = msgs[-1]["content"] if msgs else ""
    payload = {"model": model,
               "systemContent": system or None,
               "text": text}
    async with httpx.AsyncClient(proxy=proxy,
                                 timeout=CFG.DELTA_CHAT_TIMEOUT,
                                 verify=False) as c:
        r = await c.post(f"{API_BASE}/chats", json=payload,
                         headers=_auth_header(key))
    if r.status_code != 200:
        raise RuntimeError(f"delta chat HTTP {r.status_code}: {r.text[:200]}")
    out, _ = _iter_sse(r.text)
    if not out:
        raise RuntimeError("delta chat: رد فاضٍ")
    return out
TRANSLATE_SYSTEM = ("You are an expert professional translator. Output only "
                    "the translated text without any explanations, notes, or "
                    "extra text. Never mention that you are an AI.")
DETECT_SYSTEM = ("You are a language detection expert. Output only the two-"
                 "letter ISO 639-1 language code. No extra text.")
async def translate(key: str, text: str, target_lang: str,
                    model: str, proxy: str | None = None) -> str:
    prompt = (f"قم بترجمة النص التالي إلى اللغة {target_lang} بدقة عالية "
              f"مع الحفاظ على المعنى والسياق. أخرج الترجمة فقط بدون أي "
              f"إضافات أو تعليقات.\nالنص: {text}")
    out, _ = await _raw(key, model, TRANSLATE_SYSTEM, prompt, proxy)
    if not out:
        raise RuntimeError("delta translate: ما وصلت ترجمة")
    return out
async def detect_lang(key: str, text: str, model: str,
                      proxy: str | None = None) -> str:
    prompt = (f"كشف لغة النص التالي. أخرج فقط رمز اللغة المكون من حرفين "
              f"(ISO 639-1) مثل ar, en, fr. لا تخرج أي شيء آخر.\n"
              f"النص: {text}")
    out, _ = await _raw(key, model, DETECT_SYSTEM, prompt, proxy)
    return (out.strip().lower()[:2]) or "ar"
async def _raw(key, model, system, prompt, proxy):
    payload = {"model": model, "systemContent": system, "text": prompt}
    async with httpx.AsyncClient(proxy=proxy,
                                 timeout=CFG.DELTA_CHAT_TIMEOUT,
                                 verify=False) as c:
        r = await c.post(f"{API_BASE}/chats", json=payload,
                         headers=_auth_header(key))
    if r.status_code != 200:
        raise RuntimeError(f"delta chat HTTP {r.status_code}: {r.text[:200]}")
    return _iter_sse(r.text)
def is_exhausted(ex: Exception) -> bool:
    s = str(ex).lower()
    return ("401" in s or "403" in s or "unauthorized" in s
            or "forbidden" in s or "expired" in s or "token" in s)
