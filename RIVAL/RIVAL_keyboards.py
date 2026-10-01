from RIVAL_buttons import InlineKeyboard, InlineKeyboardButton, InlineKeyboardRow
from RIVAL_emojis import PREMIUM_EMOJI_IDS as P
import RIVAL_config as CFG
def _pid(ch: str) -> str:
    return P.get(ch, "")
ICON = {
    "chat":     _pid("💬"),
    "image":    _pid("🖼"),
    "tts":      _pid("🔊"),
    "music":    _pid("🎵"),
    "coder":    _pid("🐍"),
    "translate": _pid("🌐"),
    "models":   _pid("📊"),
    "main":     _pid("📂"),
    "ok":       _pid("✔️"),
    "cancel":   _pid("❌"),
    "back":     _pid("◀️"),
    "link":     _pid("🔗"),
    "phone":    _pid("📞"),
    "lock":     _pid("🔒"),
    "open":     _pid("🟢"),
    "pencil":   _pid("✍️"),
    "ban":      _pid("🚫"),
    "dev":      _pid("⚙️"),
    "status":   _pid("💎"),
}
SVC_STYLE = {"chat": "primary", "image": "primary", "tts": "primary",
             "music": "primary", "translate": "primary", "models": "primary", "coder": "primary"}
PAGE = 10
PAGE_USER = 8
def _short(name: str, n: int = 34) -> str:
    name = str(name)
    return name if len(name) <= n else name[: n - 1] + "…"
def main_menu(chat_id: int | None = None) -> InlineKeyboard:
    rows = [
        InlineKeyboardRow(
            InlineKeyboardButton("💬 محادثة", "menu:chat", style=SVC_STYLE["chat"], icon=ICON["chat"]),
            InlineKeyboardButton("🖼️ صورة", "menu:image", style=SVC_STYLE["image"], icon=ICON["image"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🔊 صوت", "menu:tts", style=SVC_STYLE["tts"], icon=ICON["tts"]),
            InlineKeyboardButton("🎵 موسيقى", "menu:music", style=SVC_STYLE["music"], icon=ICON["music"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🌐 ترجمة", "menu:translate", style=SVC_STYLE["translate"], icon=ICON["translate"]),
            InlineKeyboardButton("📚 النماذج", "mcat:0", style=SVC_STYLE["models"], icon=ICON["models"]),
        ),
    ]
    if chat_id is not None and chat_id == CFG.OWNER_ID:
        rows.append(InlineKeyboardRow(
            InlineKeyboardButton("⚙️ لوحه المطوّر", "dev:status", style="primary", icon=ICON["dev"]),
        ))
    return InlineKeyboard(*rows)
def _service_menu(kind: str, label: str) -> InlineKeyboard:
    st = SVC_STYLE[kind]
    ic = ICON[kind]
    return InlineKeyboard(
        InlineKeyboardRow(
            InlineKeyboardButton(label, f"menu:{kind}", style=st, icon=ic),
            InlineKeyboardButton("📚 تغيير النموذج", f"mtype:{kind}", style=SVC_STYLE["models"], icon=ICON["models"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("📂 الرئيسية", "menu:main", style="primary", icon=ICON["main"]),
        ),
    )
chat_menu = lambda: _service_menu("chat", "💬 محادثة")
image_menu = lambda: _service_menu("image", "🖼️ صورة")
tts_menu = lambda: _service_menu("tts", "🔊 صوت")
music_menu = lambda: _service_menu("music", "🎵 موسيقى")
coder_menu = lambda: _service_menu("coder", "🐍 برمجة")
TRANSLATE_LANGS = [
    ("ar", "العربية"), ("en", "English"), ("fr", "Français"), ("es", "Español"),
    ("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português"), ("ru", "Русский"),
    ("zh", "中文"), ("ja", "日本語"), ("ko", "한국어"), ("tr", "Türkçe"),
    ("hi", "हिन्दी"), ("ur", "اردو"), ("nl", "Nederlands"), ("pl", "Polski"),
]
def translate_menu() -> InlineKeyboard:
    return InlineKeyboard(
        InlineKeyboardRow(
            InlineKeyboardButton("🌐 ترجمة", "menu:translate", style=SVC_STYLE["translate"], icon=ICON["translate"]),
            InlineKeyboardButton("📚 تغيير النموذج", "mtype:translate", style=SVC_STYLE["models"], icon=ICON["models"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🌐 لغة الهدف", "tlangs", style=SVC_STYLE["translate"], icon=ICON["translate"]),
            InlineKeyboardButton("📂 الرئيسية", "menu:main", style="primary", icon=ICON["main"]),
        ),
    )
def translate_langs_kb(cur: str) -> InlineKeyboard:
    rows = []
    row = []
    for code, name in TRANSLATE_LANGS:
        tag = "✔ " if code == cur else "• "
        row.append(InlineKeyboardButton(f"{tag}{name}", f"tlang:{code}",
                                        style="success" if code == cur else "primary",
                                        icon=ICON["ok"] if code == cur else ICON["main"]))
        if len(row) == 2:
            rows.append(InlineKeyboardRow(*row))
            row = []
    if row:
        rows.append(InlineKeyboardRow(*row))
    rows.append(InlineKeyboardRow(
        InlineKeyboardButton("🌐 قائمة الترجمة", "menu:translate", style=SVC_STYLE["translate"], icon=ICON["translate"]),
    ))
    return InlineKeyboard(*rows)
CATEGORIES = [
    ("chat", "💬 محادثة", "chat"),
    ("translate", "🌐 ترجمة", "translate"),
    ("image", "🖼️ صورة", "image"),
    ("tts", "🔊 صوت", "tts"),
    ("music", "🎵 موسيقى", "music"),
]
def cats_page_kb(page: int) -> InlineKeyboard:
    total_pages = max(1, (len(CATEGORIES) + PAGE - 1) // PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE
    rows = []
    for i in range(0, PAGE, 2):
        row = []
        a = start + i
        if a < len(CATEGORIES):
            key, label, _ = CATEGORIES[a]
            row.append(InlineKeyboardButton(label, f"mtype:{key}", style=SVC_STYLE[key], icon=ICON[key]))
        if a + 1 < len(CATEGORIES):
            key, label, _ = CATEGORIES[a + 1]
            row.append(InlineKeyboardButton(label, f"mtype:{key}", style=SVC_STYLE[key], icon=ICON[key]))
        if row:
            rows.append(InlineKeyboardRow(*row))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ السابق", f"mcat:{page-1}", style="primary", icon=ICON["back"]))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("التالي ▶", f"mcat:{page+1}", style="primary", icon=ICON["back"]))
    nav.append(InlineKeyboardButton("📂 الرئيسية", "menu:main", style="primary", icon=ICON["main"]))
    rows.append(InlineKeyboardRow(*nav))
    return InlineKeyboard(*rows)
def models_page_kb(cat_key: str, labels: list, page: int, current_idx: int | None) -> InlineKeyboard:
    total_pages = max(1, (len(labels) + PAGE - 1) // PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE
    st = SVC_STYLE.get(cat_key, "primary")
    ic = ICON.get(cat_key, ICON["main"])
    rows = []
    for i in range(0, PAGE, 2):
        row = []
        a = start + i
        if a < len(labels):
            tag = "✔ " if current_idx == a else "• "
            sel = current_idx == a
            row.append(InlineKeyboardButton(
                f"{tag}{_short(labels[a])}", f"muse:{cat_key}:{a}",
                style="success" if sel else st, icon=ICON["ok"] if sel else ic))
        if a + 1 < len(labels):
            tag = "✔ " if current_idx == a + 1 else "• "
            sel = current_idx == a + 1
            row.append(InlineKeyboardButton(
                f"{tag}{_short(labels[a+1])}", f"muse:{cat_key}:{a+1}",
                style="success" if sel else st, icon=ICON["ok"] if sel else ic))
        if row:
            rows.append(InlineKeyboardRow(*row))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ السابق", f"mnext:{cat_key}:{page-1}", style="primary", icon=ICON["back"]))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("التالي ▶", f"mnext:{cat_key}:{page+1}", style="primary", icon=ICON["back"]))
    nav.append(InlineKeyboardButton("📂 القائمة", "menu:main", style="primary", icon=ICON["main"]))
    rows.append(InlineKeyboardRow(*nav))
    return InlineKeyboard(*rows)
def cancel_menu(kind: str) -> InlineKeyboard:
    return InlineKeyboard(
        InlineKeyboardRow(
            InlineKeyboardButton("❌ إلغاء", "menu:main", style="danger", icon=ICON["cancel"]),
        ),
    )
def contact_dev_menu() -> InlineKeyboard:
    return InlineKeyboard(
        InlineKeyboardRow(
            InlineKeyboardButton("📞 اتصال بالمطور", url=CFG.DEV_CONTACT,
                                 style="primary", icon=ICON["phone"]),
        ),
    )
def dev_menu() -> InlineKeyboard:
    return InlineKeyboard(
        InlineKeyboardRow(
            InlineKeyboardButton("📊 الحالة", "dev:status", style="primary", icon=ICON["status"]),
            InlineKeyboardButton("🔎 فحص الموفّرين", "dev:probes", style="primary", icon=ICON["models"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🟢 فتح للجميع", "dev:open", style="success", icon=ICON["open"]),
            InlineKeyboardButton("🔒 إغلاق للجميع", "dev:close", style="danger", icon=ICON["lock"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🚫 حظر / رفع", "dev:users", style="danger", icon=ICON["ban"]),
            InlineKeyboardButton("✍️ حظر برقم", "dev:banid", style="danger", icon=ICON["pencil"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("🟢 رفع برقم", "dev:unbanid", style="success", icon=ICON["ok"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("❌ مسح كل المستخدمين", "dev:clearall", style="danger", icon=ICON["cancel"]),
            InlineKeyboardButton("⚙️ إعادة الإقلاع", "dev:restart", style="primary", icon=ICON["dev"]),
        ),
        InlineKeyboardRow(
            InlineKeyboardButton("📂 الرئيسية", "menu:main", style="primary", icon=ICON["main"]),
        ),
    )
def dev_users_kb(user_ids: list, banned: set, page: int = 0) -> InlineKeyboard:
    total_pages = max(1, (len(user_ids) + PAGE_USER - 1) // PAGE_USER)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_USER
    rows = []
    chunk = user_ids[start: start + PAGE_USER]
    if not chunk:
        rows.append(InlineKeyboardRow(
            InlineKeyboardButton("لا يوجد مستخدمون مسجّلون", "dev:users",
                                 style="primary", icon=ICON["main"]),
        ))
    for i, uid in enumerate(chunk):
        us = str(uid)
        if uid in banned:
            rows.append(InlineKeyboardRow(
                InlineKeyboardButton("✔️ رفع الحظر " + us, "devunban:" + us,
                                     style="success", icon=ICON["ok"]),
            ))
        else:
            rows.append(InlineKeyboardRow(
                InlineKeyboardButton("🚫 حظر " + us, "devban:" + us,
                                     style="danger", icon=ICON["ban"]),
            ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ السابق", f"devusers:{page-1}", style="primary", icon=ICON["back"]))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("التالي ▶", f"devusers:{page+1}", style="primary", icon=ICON["back"]))
    nav.append(InlineKeyboardButton("🚫 قائمة الحظر", "dev:users", style="primary", icon=ICON["ban"]))
    nav.append(InlineKeyboardButton("⚙️ لوحه المطوّر", "dev:status", style="primary", icon=ICON["dev"]))
    rows.append(InlineKeyboardRow(*nav))
    return InlineKeyboard(*rows)
