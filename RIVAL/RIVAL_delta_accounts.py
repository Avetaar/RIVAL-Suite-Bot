import json
import os
import time
import RIVAL_config as CFG
import RIVAL_delta as DM
import RIVAL_proxies as PX
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "RIVAL_delta_accounts.json")
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
async def _new_token(chat_id: int, note: str = "") -> dict:
    rec = await DM.signup(None)
    rec["created_at"] = time.time()
    rec["rotations"] = 0
    rec["note"] = note
    data = _load()
    data[str(chat_id)] = rec
    _save(data)
    print(f"[delta-acct] توكن جديد للمستخدم {chat_id} ({note}) "
          f"صلاحية {int(rec['expiry'])}")
    return rec
def account_for(chat_id: int) -> dict | None:
    return _load().get(str(chat_id))
async def ensure_account(chat_id: int) -> tuple[str, dict]:
    if rec is None:
        rec = await _new_token(chat_id, "أول توكن")
    elif time.time() >= rec.get("expiry", 0):
        rec = await _new_token(chat_id, "تجديد صلاحية")
    return rec["key"], rec
def is_exhausted(ex: Exception) -> bool:
    return DM.is_exhausted(ex)
async def rotate(chat_id: int) -> tuple[str, dict]:
    (str(chat_id)) or {}
    rec = await _new_token(chat_id, f"تدوير {old.get('rotations', 0) + 1}")
    rec["rotations"] = old.get("rotations", 0) + 1
    data[str(chat_id)] = rec
    _save(data)
    return rec["key"], rec
