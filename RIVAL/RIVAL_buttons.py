import json
import RIVAL_emojis as _EM
_STYLE_ALIAS = {"blue": "primary", "cyan": "primary", "yellow": "primary",
                "purple": "primary", "green": "success", "orange": "success",
                "pink": "success", "red": "danger"}
_VALID_STYLES = ("primary", "success", "danger")
class InlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None, style=None,
                 icon=None, login_url=None, switch_inline_query=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.style = style
        self.icon = icon
        self.login_url = login_url
        self.switch_inline_query = switch_inline_query
    def to_dict(self):
        d = {"text": self.text}
        if self.callback_data is not None:
            d["callback_data"] = self.callback_data
        if self.url is not None:
            d["url"] = self.url
        if self.style is not None:
            st = self.style if self.style in _VALID_STYLES else _STYLE_ALIAS.get(self.style)
            if st:
                d["style"] = st
        if self.login_url is not None:
            d["login_url"] = {"url": self.login_url}
        if self.switch_inline_query is not None:
            d["switch_inline_query"] = self.switch_inline_query
        ic = self.icon or _icon_for(self.callback_data)
        if ic:
            d["icon_custom_emoji_id"] = ic
        return d
_MENU_ICONS = {"menu:chat": "bulb", "menu:image": "picture",
               "menu:tts": "bell", "menu:music": "fire",
               "menu:coder": "python", "menu:status": "gem",
               "menu:main": "crown"}
_KIND_ICONS = {"mcat": "chart", "mtype": "chart",
               "muse": "trophy", "mnext": "chart"}
def _icon_for(cb: str | None) -> str | None:
    if not cb:
        return None
    name = _MENU_ICONS.get(cb)
    if not name:
        name = _KIND_ICONS.get(cb.split(":", 1)[0])
    if not name or name not in _EM.E:
        return None
    return _EM.E[name]
class InlineKeyboardRow:
    def __init__(self, *buttons):
        self.buttons = list(buttons)
    def to_dict(self):
        return [b.to_dict() for b in self.buttons]
class InlineKeyboard:
    def __init__(self, *rows):
        self.rows = list(rows)
    def to_markup(self):
        if not self.rows:
            return None
        kb = {"inline_keyboard": [r.to_dict() for r in self.rows]}
        return json.dumps(kb, ensure_ascii=False)
    def clear(self):
        self.rows = []
