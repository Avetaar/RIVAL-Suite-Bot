import asyncio
import json
import os
import secrets
import time
import RIVAL_config as CFG
import RIVAL_gamma as GM
import RIVAL_proxies as PX
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "RIVAL_gamma_accounts.json")
_LOCK = asyncio.Lock()
def _load() -> dict:
    if os.path.exists(_PATH):
        try:
            with open(_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
def _save(data: dict) -> None:
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
def _gen_email() -> str:
    return f"r3gm_{secrets.token_hex(4)}_{int(time.time())}@gmail.com"
def _gen_password() -> str:
    return "R3_" + secrets.token_hex(8)
_BAD: set = set()
def _pick_proxies(n: int) -> list:
    if not getattr(CFG, "USE_PROXY", True):
        return []
    out = []
    for px in PX.get_proxies(n * 4):
        if px and px not in _BAD:
            out.append(px)
            if len(out) >= n:
                break
    return out
async def _try_signup(proxy: str | None) -> dict:
    res = await GM.signup(_gen_email(), _gen_password(), proxy)
    return {**res, "via_proxy": proxy or "direct"}
async def _new_user_account(chat_id: int, rotations: int = 0) -> dict:
    last = "unknown"
    for _ in range(2):
        batch = _pick_proxies(3) or [None]
        results = await asyncio.gather(*[_try_signup(p) for p in batch],
                                       return_exceptions=True)
        for res in results:
            if isinstance(res, dict):
                data = _load()
                rec = {**res, "created_at": time.time(), "rotations": rotations}
                data[str(chat_id)] = rec
                _save(data)
                print(f"[gama-acct] جديد للمستخدم {chat_id}: {res['email']} "
                      f"عبر {res.get('via_proxy', 'مباشر')} (تدوير {rotations})")
                return rec
        last = str(next(r for r in results if isinstance(r, Exception)))[
                 :120]
        for p in batch:
            if p:
                _BAD.add(p)
        await asyncio.sleep(2)
    raise RuntimeError(f"تعذر إنشاء حساب gama ({last}) — جرّب لاحقًا")
def account_for(chat_id: int) -> dict | None:
    return _load().get(str(chat_id))
async def ensure_account(chat_id: int) -> tuple[str, str]:
    async with _LOCK:
        rec = _load().get(str(chat_id))
        if rec is None:
            rec = await _new_user_account(chat_id)
        return rec["key"], rec["user_id"]
def is_exhausted(ex: Exception) -> bool:
    return GM.is_exhausted(ex)
async def rotate(chat_id: int) -> tuple[str, str]:
    async with _LOCK:
        old = _load().get(str(chat_id))
        if old:
            data = _load()
            data.pop(str(chat_id), None)
            _save(data)
        new = await _new_user_account(chat_id, (old or {}).get("rotations", 0) + 1)
        return new["key"], new["user_id"]
