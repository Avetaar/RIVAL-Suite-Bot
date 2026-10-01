import asyncio
import os
import time
import RIVAL_config as CFG
import RIVAL_state as S
import RIVAL_proxies as PX
import RIVAL_unified as U
import RIVAL_alpha as F
import RIVAL_gamma as GM
import RIVAL_delta as DL
import RIVAL_epsilon as EPS
import RIVAL_zeta as ZT
import RIVAL_pi as PI
import RIVAL_gts as GTS
import RIVAL_sigma as SIG
import RIVAL_tau as TAU
_START_TS = time.time()
LIVE_PROVIDERS = [
    ("alpha", "الموفّر الأساسي", "chat+image+tts+music+code"),
    ("gama",  "gama",    "chat"),
    ("delta", "delta",   "chat+translate"),
    ("eps",   "eps",     "chat"),
    ("zeta",  "zeta",    "chat"),
    ("pi",    "pi",      "image"),
    ("gts",   "gts",     "tts"),
    ("sig",   "sig",     "chat"),
    ("tau",   "tau",     "chat"),
]
def is_owner(chat_id: int) -> bool:
    return chat_id == CFG.OWNER_ID
def open_bot() -> str:
    S.set_bot_closed(False)
    return "✓ تم فتح البوت لجميع المستخدمين"
def close_bot() -> str:
    S.set_bot_closed(True)
    return "✓ تم إغلاق البوت لجميع المستخدمين (عدا المطوّر)"
def bot_state() -> str:
    return "مغلق للجميع" if S.bot_closed() else "مفتوح للجميع"
def ban_user(cid: int) -> str:
    S.ban_user(int(cid))
    return f"⛔ تم حظر المستخدم {cid}"
def unban_user(cid: int) -> str:
    S.unban_user(int(cid))
    return f"✓ تم رفع الحظر عن {cid}"
def banned_report() -> str:
    b = S.banned()
    return "\n".join(f"⛔ {x}" for x in sorted(b)) if b else "لا يوجد محظورون"
def users_report() -> str:
    data = S._load() if hasattr(S, "_load") else {}
    banned = S.banned()
    lines = []
    for k in sorted(data):
        if not k.isdigit():
            continue
        mark = "⛔ محظور" if k in banned else "✓ نشط"
        lines.append(f"{mark} {k}")
    return "\n".join(lines) if lines else "لا يوجد مستخدمون مسجّلون"
def uptime_str() -> str:
    s = int(time.time() - _START_TS)
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d} يوم")
    if h:
        parts.append(f"{h} ساعة")
    if m:
        parts.append(f"{m} دقيقة")
    parts.append(f"{sec} ثانية")
    return " ".join(parts[:3])
def tg_status() -> str:
    import RIVAL_api as A
    if getattr(A, "_tg_resolved", False):
        px = A.tg_proxy()
        return "مباشر" if px is None else f"بروكسي ({px})"
    return "قيد التفعيل"
def proxy_pool() -> str:
    try:
        pool = len(PX._POOL)
        verified = len(PX._VERIFIED)
        return f"{pool} حوض / {verified} موصّى"
    except Exception as ex:
        return f"غير متوفّر ({str(ex)[:40]})"
def user_stats() -> str:
    data = S._load() if hasattr(S, "_load") else {}
    users = [k for k in data if k.isdigit()]
    return f"{len(users)} مستخدم / {len(data)} مفاتيح"
async def provider_report() -> str:
    results = []
    async def probe(name: str, label: str, kinds: str) -> str:
        ok, detail = False, ""
        try:
            if name == "alpha":
                ms = await asyncio.wait_for(F.all_models(), 25)
                usable = sum(len(F.models_by_type(ms, t))
                             for t in ("chat", "image", "tts", "music", "code"))
                ok, detail = True, f"{usable} نموذج عملي"
            elif name == "gama":
                n = len(GM.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            elif name == "delta":
                n = len(DL.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            elif name == "eps":
                n = len(EPS.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            elif name == "zeta":
                n = len(ZT.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            elif name == "pi":
                n = len(PI.models_by_type("image"))
                ok, detail = True, f"{n} نموذج"
            elif name == "gts":
                n = len(GTS.models_by_type("tts"))
                ok, detail = True, f"{n} نموذج"
            elif name == "sig":
                n = len(SIG.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            elif name == "tau":
                n = len(TAU.models_by_type("chat"))
                ok, detail = True, f"{n} نموذج"
            else:
                ok, detail = True, "—"
        except Exception as ex:
            detail = str(ex)[:50]
        results.append((name, label, "✔" if ok else "✘", detail))
    coros = [probe(n, lb, k) for (n, lb, k) in LIVE_PROVIDERS]
    await asyncio.gather(*coros)
    lines = []
    for name, label, mark, detail in results:
        lines.append(f"{mark} {label} ({name}) — {detail}")
    return "\n".join(lines)
async def full_report(chat_id: int) -> str:
    prov = await provider_report()
    return (
        "📊 لوحه الحالة — RIVAL\n"
        "─────────────\n"
        f"⏱️ التشغيل: {uptime_str()}\n"
        f"🔌 تيليجرام: {tg_status()}\n"
        f"🛰️ البروكسي: {proxy_pool()}\n"
        f"👥 المستخدمون: {user_stats()}\n"
        f"🚦 حالة البوت: {bot_state()}\n"
        f"🔢 الموفّرون: {len(LIVE_PROVIDERS)} مفعّل\n"
        "─────────────\n"
        "فحص الموفّرين:\n"
        f"{prov}"
    )
def clear_user(chat_id: int) -> str:
    data = S._load() if hasattr(S, "_load") else {}
    key = str(chat_id)
    if key in data:
        del data[key]
        S._save(data)
        return "✓ تم مسح الحالة"
    return "— ماكو حالة مسجّلة لهذا المستخدم"
def clear_all_users() -> str:
    data = S._load() if hasattr(S, "_load") else {}
    users = [k for k in data if k.isdigit()]
    for k in users:
        data.pop(k, None)
    S._save(data)
    return f"✓ تم مسح {len(users)} حالة مستخدم"
def reset_proxies() -> str:
    try:
        n = PX.update(True)
        return f"✓ تجديد الحوض: {n} بروكسي"
    except Exception as ex:
        return f"✘ فشل التجديد: {str(ex)[:60]}"
def restart_bot() -> str:
    global _RESTART
    _RESTART = True
    return "✓ تم طلب إعادة الإقلاع — سيبدأ البوت من جديد خلال لحظات"
_RESTART = False
def request_restart() -> bool:
    return _RESTART
def clear_restart() -> None:
    global _RESTART
    _RESTART = False
