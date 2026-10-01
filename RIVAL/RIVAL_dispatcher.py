import RIVAL_api as A
import RIVAL_config as CFG
import RIVAL_state as S
import RIVAL_handlers as H
import RIVAL_keyboards as K
import RIVAL_devboard as DEV
from RIVAL_emojis import EMO, esc
PROMPTS = {
    "chat": EMO('bulb') + " أرسل سؤالك للمحادثة 👇",
    "translate": EMO('globe') + " أرسل أي نص ويرتفع كشف لغته وترجمته تلقائيًا إلى لغتك الهدف 👇",
    "image": EMO('picture') + " أرسل وصف الصورة التي تريدها 👇\n(مثال: علم العراق في الفضاء)",
    "tts": EMO('bell') + " أرسل النص الذي تريد تحويله إلى صوت 👇",
    "music": EMO('fire') + " أرسل وصف الموسيقى التي تريدها 👇\n(مثال: أغنية عراقية حماسية)",
    "coder": EMO('python') + " أرسل طلبك البرمجي 👇",
}
MODE_KB = {
    "chat": K.chat_menu,
    "translate": K.translate_menu,
    "image": K.image_menu,
    "tts": K.tts_menu,
    "music": K.music_menu,
    "coder": K.coder_menu,
}
MODEL_TYPE = {
    "chat": "chat", "translate": "translate", "image": "image", "tts": "tts",
    "music": "music", "coder": "code",
}
async def dispatch_callback(cb: dict, chat_id: int, mid: int) -> None:
    data = cb.get("data", "") or ""
    kind, _, arg = data.partition(":")
    if kind == "menu":
        if arg == "main":
            S.clear_mode(chat_id)
            await A.edit(chat_id, mid, H.WELCOME, K.main_menu(chat_id))
        elif arg == "status":
            S.clear_mode(chat_id)
            await A.edit(chat_id, mid, H.WELCOME, K.main_menu(chat_id))
        elif arg == "models":
            await A.edit(chat_id, mid, EMO('chart') + " ✦ جاري فتح فهرس النماذج...",
                         K.cats_page_kb(0))
        elif arg in MODE_KB:
            S.set_mode(chat_id, arg)
            await A.edit(chat_id, mid, PROMPTS[arg], MODE_KB[arg]())
        else:
            S.clear_mode(chat_id)
            await A.edit(chat_id, mid, H.WELCOME, K.main_menu(chat_id))
    elif kind == "mcat":
        page = int(arg)
        await A.edit(chat_id, mid, "📚 اختر فئة النماذج:", K.cats_page_kb(page))
    elif kind == "tlangs":
        cur = S.translate_lang(chat_id)
        await A.edit(chat_id, mid, EMO('globe') + " اختر لغة الهدف:",
                     K.translate_langs_kb(cur))
    elif kind == "tlang":
        S.set_translate_lang(chat_id, arg)
        name = dict(K.TRANSLATE_LANGS).get(arg, arg)
        await A.edit(chat_id, mid,
                     EMO('check') + " ✦ لغة الهدف: " + esc(name, 20)
                     + "\nاضغط خدمة للاستخدام", K.translate_menu())
    elif kind == "mtype":
        tid = arg
        await H.show_model_page(chat_id, mid, tid, 0)
    elif kind == "muse":
        parts = arg.split(":", 1)
        tid = parts[0]
        idx = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        await H.select_model(chat_id, mid, tid, idx)
    elif kind == "mnext":
        parts = arg.split(":", 1)
        tid = parts[0]
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        await H.show_model_page(chat_id, mid, tid, page)
    elif kind == "dev":
        if not DEV.is_owner(chat_id):
            await A.answer(cb["id"], "غير مصرّح")
            return
        if arg == "status":
            await A.edit(chat_id, mid, EMO('settings') + " ✦ لوحه المطوّر\n⏳ جارٍ تجميع الحالة...",
                         K.dev_menu())
            report = await DEV.full_report(chat_id)
            await A.edit(chat_id, mid, report, K.dev_menu())
        elif arg == "probes":
            await A.edit(chat_id, mid, EMO('chart') + " ✦ جارٍ فحص الموفّرين...",
                         K.dev_menu())
            prov = await DEV.provider_report()
            await A.edit(chat_id, mid, "🔎 حالة الموفّرين:\n" + prov, K.dev_menu())
        elif arg == "open":
            res = DEV.open_bot()
            await A.edit(chat_id, mid, EMO('check') + " " + res, K.dev_menu())
        elif arg == "close":
            res = DEV.close_bot()
            await A.edit(chat_id, mid, EMO('check') + " " + res, K.dev_menu())
        elif arg == "users":
            data = S._load() if hasattr(S, "_load") else {}
            uids = sorted([k for k in data if k.isdigit()])
            banned = S.banned()
            await A.edit(chat_id, mid,
                         EMO('people') + " اختر مستخدمًا للحظر أو رفع الحظر:\n"
                         + DEV.users_report(),
                         K.dev_users_kb(uids, banned, 0))
        elif arg == "banid":
            S.set_dev_pending(chat_id, "ban")
            await A.edit(chat_id, mid,
                         EMO('pencil') + " أرسل رقم معرف المستخدم لتحظره (أو ❌ للإلغاء)",
                         K.dev_menu())
        elif arg == "unbanid":
            S.set_dev_pending(chat_id, "unban")
            await A.edit(chat_id, mid,
                         EMO('pencil') + " أرسل رقم معرف المستخدم لرفع الحظر (أو ❌ للإلغاء)",
                         K.dev_menu())
        elif arg == "clearall":
            res = DEV.clear_all_users()
            await A.edit(chat_id, mid, EMO('people') + " " + res, K.dev_menu())
        elif arg == "restart":
            DEV.request_restart()
            await A.edit(chat_id, mid, EMO('settings') + " ✓ تم طلب إعادة الإقلاع — سيرتفع البوت من جديد.",
                         K.dev_menu())
        else:
            await A.edit(chat_id, mid, EMO('settings') + " ✦ لوحه المطوّر", K.dev_menu())
    elif kind == "devusers":
        if not DEV.is_owner(chat_id):
            await A.answer(cb["id"], "غير مصرّح")
            return
        page = int(arg) if arg.isdigit() else 0
        data = S._load() if hasattr(S, "_load") else {}
        uids = sorted([k for k in data if k.isdigit()])
        banned = S.banned()
        await A.edit(chat_id, mid,
                     EMO('people') + " اختر مستخدمًا للحظر أو رفع الحظر:\n"
                     + DEV.users_report(),
                     K.dev_users_kb(uids, banned, page))
    elif kind == "devban" or kind == "devunban":
        if not DEV.is_owner(chat_id):
            await A.answer(cb["id"], "غير مصرّح")
            return
        target = int(arg)
        res = DEV.ban_user(target) if kind == "devban" else DEV.unban_user(target)
        await A.edit(chat_id, mid, EMO('check') + " " + res + "\n" + DEV.banned_report(),
                     K.dev_menu())
    else:
        S.clear_mode(chat_id)
        await A.edit(chat_id, mid, H.WELCOME, K.main_menu(chat_id))
