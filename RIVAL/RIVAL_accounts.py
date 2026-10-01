import asyncio
import json
import os
import re
import secrets
import time
import httpx
import RIVAL_config as CFG
import RIVAL_alpha as F
import RIVAL_proxies as PX
UA_WEB = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
EMAIL_DOMAIN = "gmail.com"
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), CFG.ACCOUNTS_FILE)
_LOCK = asyncio.Lock()
def _load() -> dict:
    if os.path.exists(_PATH):
        try:
            with open(_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}
def _save(data: dict) -> None:
    with open(_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
def _gen_email() -> str:
    return f"r3avetaar_{secrets.token_hex(6)}_{int(time.time())}@{EMAIL_DOMAIN}"
def _gen_password() -> str:
    return "R3_" + secrets.token_hex(10)
def _signup_sync(email: str, password: str, proxy: str | None = None,
                 timeout: int = 40) -> dict:
    kw = {"proxy": proxy} if proxy else {}
    c = httpx.Client(timeout=timeout, follow_redirects=False,
                     headers={"User-Agent": UA_WEB}, **kw)
    try:
        r = c.get(CFG.SITE_BASE + "/signup/")
        csrf = re.search(r'name="csrfmiddlewaretoken"[^>]*value="([^"]+)"', r.text).group(1)
        stok = re.search(r'name="signup_token"[^>]*value="([^"]+)"', r.text).group(1)
        p = c.post(
            CFG.SITE_BASE + "/signup/",
            data={"csrfmiddlewaretoken": csrf, "lang": "en",
                  "signup_token": stok, "email": email, "password": password},
            headers={"Referer": CFG.SITE_BASE + "/signup/",
                     "X-CSRFToken": csrf, "Origin": CFG.SITE_BASE},
            follow_redirects=False,
        )
        if p.status_code == 429:
            raise RuntimeError("signup rate-limited (429)")
        if p.status_code == 200:
            raise RuntimeError(f"signup rejected (200, stayed on form)")
        st = c.post(
            CFG.SITE_BASE + "/api/v1/session-token/",
            headers={"X-CSRFToken": c.cookies.get("csrftoken", ""),
                     "X-Requested-With": "XMLHttpRequest",
                     "Referer": CFG.SITE_BASE + "/"},
            follow_redirects=False,
        )
        if "json" not in (st.headers.get("content-type") or ""):
            raise RuntimeError(f"session-token غير JSON: {st.text[:80]}")
        d = st.json()
        key = d.get("api_key")
        if not key:
            raise RuntimeError(f"no api_key: {str(d)[:120]}")
        return {"api_key": key, "email": email, "password": password,
                "via_proxy": proxy or "direct"}
    finally:
        c.close()
def _delete_sync(email: str, password: str, proxy: str | None = None) -> bool:
    kw = {"proxy": proxy} if proxy else {}
    try:
        c = httpx.Client(timeout=30, follow_redirects=False,
                         headers={"User-Agent": UA_WEB}, **kw)
        try:
            r = c.get(CFG.SITE_BASE + "/login/")
            m = re.search(r'name="csrfmiddlewaretoken"[^>]*value="([^"]+)"', r.text)
            csrf = m.group(1) if m else ""
            c.post(CFG.SITE_BASE + "/login/",
                   data={"csrfmiddlewaretoken": csrf, "email": email,
                         "password": password},
                   headers={"Referer": CFG.SITE_BASE + "/login/",
                            "X-CSRFToken": csrf, "Origin": CFG.SITE_BASE},
                   follow_redirects=False)
            c.get(CFG.SITE_BASE + "/delete-account/",
                  params={"confirm_email": "DELETE", "password": ""},
                  headers={"X-CSRFToken": c.cookies.get("csrftoken", ""),
                           "Referer": CFG.SITE_BASE + "/account/"},
                  follow_redirects=False)
            return True
        finally:
            c.close()
    except Exception:
        return False
async def create_account(proxy: str | None = None, timeout: int = 40) -> dict:
    return await asyncio.to_thread(_signup_sync, _gen_email(), _gen_password(),
                                   proxy, timeout)
_BAD: set = set()
def _pick_proxies(n: int) -> list:
    if not getattr(CFG, "USE_PROXY", True):
        return []
    out = []
    for px in PX.get_proxies(n * 4):
        if px not in _BAD:
            out.append(px)
            if len(out) >= n:
                break
    return out
async def _try_signup(proxy: str | None) -> dict:
    try:
        return await create_account(proxy, timeout=30)
    except Exception:
        if proxy:
            _BAD.add(proxy)
        raise
async def _new_user_account(chat_id: int, rotations: int = 0) -> dict:
    last = "unknown"
    for _ in range(3):
        batch = _pick_proxies(3) or [None]
        results = await asyncio.gather(*[_try_signup(p) for p in batch],
                                       return_exceptions=True)
        for res in results:
            if isinstance(res, dict):
                data = _load()
                rec = {**res, "created_at": time.time(), "rotations": rotations}
                data[str(chat_id)] = rec
                _save(data)
                print(f"[accounts] جديد للمستخدم {chat_id}: {res['email']} "
                      f"عبر {res.get('via_proxy', 'مباشر')} (تدوير {rotations})")
                return rec
        last = next(str(r) for r in results if not isinstance(r, dict))
        await asyncio.sleep(3)
    raise RuntimeError(f"تعذر إنشاء حساب ({last}) — جرّب لاحقًا")
def account_for(chat_id: int) -> dict | None:
    return _load().get(str(chat_id))
async def ensure_account(chat_id: int) -> str:
    async with _LOCK:
        rec = _load().get(str(chat_id))
        if rec is None:
            rec = await _new_user_account(chat_id)
        return rec["api_key"]
async def _delete_sync_async(rec: dict) -> bool:
    px = None if not getattr(CFG, "USE_PROXY", True) else PX.get_proxy()
    return await asyncio.to_thread(_delete_sync,
                            rec.get("email", ""), rec.get("password", ""), px)
async def rotate(chat_id: int) -> str:
    async with _LOCK:
        old = _load().get(str(chat_id))
        if old:
            await _delete_sync_async(old)
        new = await _new_user_account(chat_id, (old or {}).get("rotations", 0) + 1)
        return new["api_key"]
def is_credit_error(ex: Exception) -> bool:
    s = str(ex).lower()
    return ("402" in s or "429" in s or "payment" in s or
            "balance" in s or "credits" in s or "tokens" in s and "purchase" in s or
            "rate-limited" in s or "rate limit" in s)
