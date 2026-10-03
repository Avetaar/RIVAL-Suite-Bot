import json
import os
import time
import RIVAL_config as CFG
_path = os.path.join(os.path.dirname(__file__), CFG.DB_FILE)
def _load() -> dict:
    if os.path.exists(_path):
        try:
            with open(_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
def _save(data: dict) -> None:
    with open(_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
def ensure(chat_id: int) -> dict:
    data = _load()
    key = str(chat_id)
    if key not in data:
        data[key] = {"mode": None, "history": [], "coder_session": None}
        _save(data)
    return data[key]
def get(chat_id: int) -> dict:
    return ensure(chat_id)
def set_mode(chat_id: int, mode: str | None) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None})["mode"] = mode
    _save(data)
def clear_mode(chat_id: int) -> None:
    set_mode(chat_id, None)
def history(chat_id: int) -> list:
    return get(chat_id).get("history", [])
def set_history(chat_id: int, hist: list) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None})[
        "history"] = hist[-(CFG.CHAT_HISTORY_DEPTH * 2):]
    _save(data)
def set_coder_session(chat_id: int, sid: str) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None})["coder_session"] = sid
    _save(data)
def set_model(chat_id: int, type_id: str, model: str) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None}) \
        .setdefault("models", {})[type_id] = model
    _save(data)
def model_for(chat_id: int, type_id: str) -> str | None:
    return get(chat_id).get("models", {}).get(type_id)
def set_translate_lang(chat_id: int, code: str) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None})[
        "translate_lang"] = code
    _save(data)
def translate_lang(chat_id: int) -> str:
    return get(chat_id).get("translate_lang") or "ar"
_IMAGE_BUF: dict = {}
def set_image(chat_id: int, data: bytes) -> None:
    _IMAGE_BUF[str(chat_id)] = data
def get_image(chat_id: int):
    return _IMAGE_BUF.get(str(chat_id))
def clear_image(chat_id: int) -> None:
    _IMAGE_BUF.pop(str(chat_id), None)
def set_quick_action(chat_id: int, action: str) -> None:
    data = _load()
    data.setdefault(str(chat_id), {"mode": None, "history": [], "coder_session": None})[
        "quick_action"] = action
    _save(data)
def quick_action(chat_id: int) -> str | None:
    return get(chat_id).get("quick_action")
def bot_closed() -> bool:
    data = _load()
    return bool(data.get("__bot_closed__"))
def set_bot_closed(v: bool) -> None:
    data = _load()
    data["__bot_closed__"] = bool(v)
    _save(data)
def banned() -> set:
    data = _load()
    return set(data.get("__banned__", []))
def ban_user(cid: int) -> None:
    data = _load()
    cur = set(data.get("__banned__", []))
    cur.add(str(cid))
    data["__banned__"] = sorted(cur)
    _save(data)
def unban_user(cid: int) -> None:
    data = _load()
    cur = set(data.get("__banned__", []))
    cur.discard(str(cid))
    data["__banned__"] = sorted(cur)
    _save(data)
def is_banned(cid: int) -> bool:
    return str(cid) in banned()
def set_dev_pending(cid: int, action: str | None) -> None:
    data = _load()
    data.setdefault(str(cid), {"mode": None, "history": [], "coder_session": None})[
        "dev_pending"] = action
    data[str(cid)]["dev_pending_at"] = time.time() if action else 0.0
    _save(data)
def dev_pending(cid: int) -> str | None:
    st = get(cid)
    act = st.get("dev_pending")
    if not act:
        return None
    if time.time() - float(st.get("dev_pending_at") or 0) > 300:
        st["dev_pending"] = None
        st["dev_pending_at"] = 0.0
        _save(st)
        return None
    return act
