import asyncio
import ctypes
import json
import os
import subprocess
import sys
import importlib
import httpx
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "RIVAL"))
_HERE = os.path.dirname(os.path.abspath(__file__))
def _load_credentials() -> dict:
    candidates = [
        os.path.join(_HERE, "RIVAL", "bot_credentials.json"),
        os.path.join(_HERE, "bot_credentials.json"),
        os.path.expanduser("~/.rival_bot_credentials.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                pass
    return {}
_cred = _load_credentials()
TOKEN = str(os.environ.get("RIVAL_BOT_TOKEN") or _cred.get("token") or "").strip()
OWNER_ID = int(os.environ.get("RIVAL_OWNER_ID") or _cred.get("owner_id") or 0)
OWNER_USERNAME = str(os.environ.get("RIVAL_OWNER_USERNAME") or _cred.get("owner_username") or "").strip()
import RIVAL_config as CFG
CFG.TOKEN = TOKEN
CFG.OWNER_ID = OWNER_ID or 0
if OWNER_USERNAME:
    CFG.DEV_CONTACT = "https://t.me/" + OWNER_USERNAME
if OWNER_ID:
    CFG.ALLOW_IDS = {OWNER_ID}
import RIVAL_api as A
import RIVAL_dispatcher as D
import RIVAL_handlers as H
import RIVAL_keyboards as K
import RIVAL_devboard as DEV
import RIVAL_alpha as F
import RIVAL_proxies as PX
import RIVAL_state as S
DEPS = {"httpx": "httpx", "PIL": "Pillow"}
_MUX_HANDLE = None
_BOT_USERNAME = ""
def _bootstrap() -> None:
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "RIVAL", "RIVAL_requirements.txt")
    missing = []
    for mod in ("httpx", "PIL"):
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print("installing:", missing)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])
        importlib.invalidate_caches()
        importlib.reload(sys.modules["RIVAL_api"])
        importlib.reload(sys.modules["RIVAL_config"])
        importlib.reload(sys.modules["RIVAL_dispatcher"])
        importlib.reload(sys.modules["RIVAL_handlers"])
        importlib.reload(sys.modules["RIVAL_keyboards"])
        importlib.reload(sys.modules["RIVAL_devboard"])
def _acquire_lock() -> None:
    global _MUX_HANDLE
    lock_name = "AvetaarR3lSuiteBot"
    try:
        import time as _time
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k32.CreateMutexW.restype = ctypes.c_void_p
        k32.GetLastError.argtypes = []
        k32.GetLastError.restype = ctypes.c_ulong
        for _ in range(10):
            _MUX_HANDLE = k32.CreateMutexW(None, lock_name)
            if k32.GetLastError() == 183:
                _time.sleep(2)
                continue
            return
        print("STOP: a second bot instance is running")
        sys.exit(0)
    except Exception:
        pass
    lock_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             ".avetaar_bot.lock")
    try:
        import fcntl
        _MUX_HANDLE = open(lock_path, "w")
        _MUX_HANDLE.write(str(os.getpid()))
        _MUX_HANDLE.flush()
        fcntl.flock(_MUX_HANDLE.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        print("STOP: a second bot instance is running")
        sys.exit(0)
def _gate(chat_id: int, text: str | None = None, is_group: bool = False) -> str:
    if chat_id == OWNER_ID:
        return "allow"
    if S.is_banned(chat_id):
        return "banned"
    if S.bot_closed():
        return "closed"
    if getattr(CFG, "PUBLIC", False):
        if is_group and text is not None:
            t = text.strip()
            ok = t.startswith("/") or (t and _BOT_USERNAME and "@" + _BOT_USERNAME in t)
            return "allow" if ok else "deny"
        return "allow"
    return "allow" if chat_id in CFG.ALLOW_IDS else "deny"
async def _handle(update: dict) -> None:
    msg = update.get("message")
    if msg and msg.get("text"):
        chat = msg["chat"]
        chat_id = chat["id"]
        text = msg["text"]
        is_group = chat.get("type") in ("group", "supergroup")
        status = _gate(chat_id, text, is_group)
        if status != "allow":
            if status in ("closed", "banned"):
                await H.gate_reply(chat_id, status)
            return
        if is_group and _BOT_USERNAME:
            text = text.replace("@" + _BOT_USERNAME, "").strip()
        await H.on_text(chat_id, text)
        return
    if msg and (msg.get("photo") or msg.get("document")):
        chat_id = msg["chat"]["id"]
        status = _gate(chat_id, None, False)
        if status != "allow":
            if status in ("closed", "banned"):
                await H.gate_reply(chat_id, status)
            return
        await H.on_photo(chat_id, msg)
        return
    cb = update.get("callback_query")
    if cb:
        chat_id = cb["message"]["chat"]["id"]
        status = _gate(chat_id, None, False)
        if status != "allow":
            if status in ("closed", "banned"):
                await H.gate_reply(chat_id, status)
            return
        mid = cb["message"]["message_id"]
        await A.answer(cb["id"])
        await D.dispatch_callback({"data": cb.get("data", "")}, chat_id, mid)
async def _loop() -> None:
    global _BOT_USERNAME
    offset = 0
    c = httpx.AsyncClient(proxy=A.tg_proxy(), timeout=70)
    fails = 0
    while True:
        try:
            r = await c.post(A._bot_url("getUpdates"),
                             json={"offset": offset, "timeout": 50})
            data = r.json()
            fails = 0
        except Exception as ex:
            fails += 1
            print("poll error:", type(ex).__name__, str(ex)[:60])
            A.reset_tg_proxy()
            await A._resolve_tg_proxy()
            try:
                c.close()
            except Exception:
                pass
            c = httpx.AsyncClient(proxy=A.tg_proxy(), timeout=70)
            if fails >= 20:
                print("poll: 20 failures - cooling down 60s")
                fails = 0
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(3)
            continue
        if not data.get("ok"):
            print("getUpdates rejected:", data.get("error_code"),
                  data.get("description"))
            if data.get("error_code") == 409:
                print("-> another server reads the same bot")
                sys.exit(1)
            await asyncio.sleep(5)
            continue
        for u in data.get("result", []):
            offset = u["update_id"] + 1
            print("[update]", u["update_id"], u.get("message", {}).get("text", "")[:30] if u.get("message") else "callback")
            try:
                await _handle(u)
            except Exception as ex:
                print("handler error:", ex)
        if DEV.request_restart():
            print("[dev] restart requested from devboard - re-exec")
            c.close()
            if os.name == "nt":
                subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd())
                os._exit(0)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        await asyncio.sleep(0.3)
def _warm_models() -> None:
    async def _run() -> None:
        try:
            ms = await F.all_models()
            print(f"[models] cache ready: {len(ms)}")
        except Exception as ex:
            print(f"[models] warm failed ({ex})")
    asyncio.create_task(_run())
def _warm_proxies() -> None:
    async def _run() -> None:
        try:
            n = await asyncio.to_thread(PX.update, True)
            print(f"[proxies] pool ready: {n}")
        except Exception as ex:
            print(f"[proxies] refresh failed ({ex}) - using stored pool")
    asyncio.create_task(_run())
async def main() -> None:
    global _BOT_USERNAME
    _bootstrap()
    if not TOKEN:
        print("TOKEN is empty - run install.sh (creates RIVAL/bot_credentials.json)")
        print("or set RIVAL_BOT_TOKEN, RIVAL_OWNER_ID, RIVAL_OWNER_USERNAME env vars")
        return
    if not OWNER_ID:
        print("OWNER_ID is missing - run install.sh or set RIVAL_OWNER_ID")
        return
    _acquire_lock()
    me = {}
    for i in range(10):
        try:
            me = await A.me()
            if me:
                break
        except Exception as ex:
            print(f"getMe attempt {i + 1} failed: {ex}")
            await asyncio.sleep(5)
    if not me:
        print("STOP: cannot reach Telegram after 10 attempts.")
        sys.exit(1)
    _BOT_USERNAME = me.get("username") or ""
    print("bot:", _BOT_USERNAME)
    print("public mode:", "open to all" if getattr(CFG, "PUBLIC", False)
          else "restricted to: " + str(CFG.ALLOW_IDS))
    _warm_proxies()
    _warm_models()
    from RIVAL_emojis import EMO
    await A.message(OWNER_ID,
                    EMO('sparkles') + " ✦ Avetaar assistant ready ✦ "
                    + EMO('fire') + "\nUnified providers - pick a service 👇",
                    K.main_menu(OWNER_ID))
    await _loop()
if __name__ == "__main__":
    asyncio.run(main())
