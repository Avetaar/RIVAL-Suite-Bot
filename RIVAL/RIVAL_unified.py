import json
import os
import RIVAL_config as CFG
import RIVAL_alpha as F
import RIVAL_gamma as GM
import RIVAL_gamma_accounts as GAACCT
import RIVAL_delta as DL
import RIVAL_delta_accounts as DLACCT
import RIVAL_epsilon as EPS
import RIVAL_zeta as ZT
import RIVAL_pi as PI
import RIVAL_gts as GTS
import RIVAL_sigma as SIG
import RIVAL_tau as TAU
import RIVAL_accounts as ACCT
import RIVAL_proxies as PX
PROV_FREE = "free"
PROV_GAMA = "gama"
PROV_DELTA = "delta"
PROV_EPS = "eps"
PROV_ZETA = "zeta"
PROV_PI = "pi"
PROV_GTS = "gts"
PROV_SIG = "sig"
PROV_TAU = "tau"
_SUP = "¹²³⁴⁵⁶⁷⁸⁹"
def parse(ref: str) -> tuple[str, str]:
    if ":" in ref:
        p, m = ref.split(":", 1)
        return (p, m)
    return (PROV_FREE, ref)
def label_of(ref: str) -> str:
    prov, mid = parse(ref)
    if prov == PROV_GAMA:
        return GM.display_label(mid)
    if prov == PROV_DELTA:
        return DL.display_label(mid)
    if prov == PROV_EPS:
        return EPS.display_label(mid)
    if prov == PROV_ZETA:
        return ZT.display_label(mid)
    if prov == PROV_PI:
        return PI.display_label(mid)
    if prov == PROV_GTS:
        return GTS.display_label(mid)
    if prov == PROV_SIG:
        return SIG.display_label(mid)
    if prov == PROV_TAU:
        return TAU.display_label(mid)
    return mid
_CATMAP = {
    "chat":      ("chat", "chat", "chat", "chat", "chat", None, None, "chat", "chat", None),
    "image":     ("image", None, None, None, None, "image", None, None, None, None),
    "tts":       ("tts", None, None, None, None, None, "tts", None, None, None),
    "music":     ("music", None, None, None, None, None, None, None, None, None),
    "coder":     ("code", None, None, None, None, None, None, None, None, None),
    "translate": (None, None, "chat", None, None, None, None, None, None, None),
}
_BLOCKED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "RIVAL_blocked_models.json")
def _load_blocked() -> set:
    try:
        with open(_BLOCKED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()
def _dedup(entries: list) -> list:
    seen: dict = {}
    out = []
    for ref, lab in entries:
        c = seen.get(lab, 0)
        seen[lab] = c + 1
        if c == 0:
            out.append((ref, lab))
        else:
            out.append((ref, lab + _SUP[c - 1] if c - 1 < len(_SUP) else lab))
    return out
async def unified_models(cat: str) -> list:
    ftype, gama_type, d_type, e_type, z_type, p_type, g_type, sig_type, tau_type, flt = \
        _CATMAP.get(cat, (cat,) + (None,) * 9)
    out = []
    if ftype:
        try:
            ms = await F.all_models()
            for mid in F.models_by_type(ms, ftype):
                if mid in _load_blocked():
                    continue
                out.append((f"{PROV_FREE}:{mid}", mid))
        except Exception:
            pass
    if gama_type:
        for mid in GM.models_by_type(gama_type):
            out.append((f"{PROV_GAMA}:{mid}", GM.display_label(mid)))
    if d_type:
        for mid in DL.models_by_type(d_type):
            out.append((f"{PROV_DELTA}:{mid}", DL.display_label(mid)))
    if e_type:
        for mid in EPS.models_by_type(e_type):
            out.append((f"{PROV_EPS}:{mid}", EPS.display_label(mid)))
    if z_type:
        for mid in ZT.models_by_type(z_type):
            out.append((f"{PROV_ZETA}:{mid}", ZT.display_label(mid)))
    if p_type:
        for mid in PI.models_by_type(p_type):
            out.append((f"{PROV_PI}:{mid}", PI.display_label(mid)))
    if g_type:
        for mid in GTS.models_by_type(g_type):
            out.append((f"{PROV_GTS}:{mid}", GTS.display_label(mid)))
    if sig_type:
        for mid in SIG.models_by_type(sig_type):
            out.append((f"{PROV_SIG}:{mid}", SIG.display_label(mid)))
    if tau_type:
        for mid in TAU.models_by_type(tau_type):
            out.append((f"{PROV_TAU}:{mid}", TAU.display_label(mid)))
    return _dedup(out)
async def unified_ids(cat: str) -> list:
    return [r[0] for r in await unified_models(cat)]
def default_ref(cat: str) -> str:
    return {
        "chat": f"{PROV_FREE}:{CFG.DEFAULT_CHAT_MODEL}",
        "image": f"{PROV_FREE}:{CFG.IMAGE_MODEL}",
        "tts": f"{PROV_FREE}:{CFG.TTS_MODEL}",
        "music": f"{PROV_FREE}:ace-step",
        "coder": f"{PROV_FREE}:{CFG.CODER_MODEL}",
        "translate": f"{PROV_DELTA}:gpt-5-nano",
    }.get(cat, f"{PROV_FREE}:standard")
async def _gama_call(chat_id: int, caller):
    key, uid = await GAACCT.ensure_account(chat_id)
    try:
        return await caller(key, uid, None)
    except Exception as ex:
        if GAACCT.is_exhausted(ex):
            key, uid = await GAACCT.rotate(chat_id)
            return await caller(key, uid, None)
        msg = str(ex).lower()
        if "connect" in msg or "proxy" in msg:
            return await caller(key, uid, PX.get_proxy())
        raise
async def _delta_call(chat_id: int, caller):
    key, _rec = await DLACCT.ensure_account(chat_id)
    try:
        return await caller(key, _rec, None)
    except Exception as ex:
        if DLACCT.is_exhausted(ex):
            key, _rec = await DLACCT.rotate(chat_id)
            return await caller(key, _rec, None)
        msg = str(ex).lower()
        if "connect" in msg or "proxy" in msg:
            return await caller(key, _rec, PX.get_proxy())
        raise
async def _eps_call(chat_id: int, model: str, messages: list) -> str:
    try:
        return await EPS.chat(messages, model)
    except Exception as ex:
        if EPS.is_exhausted(ex):
            return await EPS.chat(messages, model, proxy=PX.get_proxy())
        raise
async def _zeta_call(chat_id: int, model: str, messages: list) -> str:
    try:
        return await ZT.chat(messages, model)
    except Exception as ex:
        if ZT.is_exhausted(ex):
            return await ZT.chat(messages, model, proxy=PX.get_proxy())
        raise
class ServiceBusy(Exception):
    pass
async def _alpha_silent(chat_id: int, fn, *args, max_rotations: int = 2, **kw):
    key = await ACCT.ensure_account(chat_id)
    last = None
    for attempt in range(max_rotations + 1):
        try:
            return await fn(key, *args, **kw)
        except Exception as ex:
            last = ex
            if ACCT.is_credit_error(ex) and attempt < max_rotations:
                key = await ACCT.rotate(chat_id)
                continue
            raise
    raise ServiceBusy() from last
async def chat(chat_id: int, ref: str, prompt: str,
               history: list) -> str:
    prov, mid = parse(ref)
    if prov == PROV_GAMA:
        async def _c(key, uid, px):
            msgs = list(history) if history else [{"role": "user", "content": prompt}]
            return await GM.chat(key, uid, mid, msgs, proxy=px)
        return await _gama_call(chat_id, _c)
    if prov == PROV_DELTA:
        async def _c(key, rec, px):
            msgs = list(history) if history else [{"role": "user", "content": prompt}]
            return await DL.chat(key, mid, msgs, proxy=px)
        return await _delta_call(chat_id, _c)
    if prov == PROV_EPS:
        msgs = list(history) if history else [{"role": "user", "content": prompt}]
        return await _eps_call(chat_id, mid, msgs)
    if prov == PROV_ZETA:
        msgs = list(history) if history else [{"role": "user", "content": prompt}]
        return await _zeta_call(chat_id, mid, msgs)
    if prov == PROV_SIG:
        msgs = list(history) if history else [{"role": "user", "content": prompt}]
        try:
            return await SIG.chat(mid, msgs, tg_id=chat_id)
        except Exception as ex:
            if SIG.is_exhausted(ex):
                return await SIG.chat(mid, msgs, proxy=PX.get_proxy(), tg_id=chat_id)
            raise
    if prov == PROV_TAU:
        msgs = list(history) if history else [{"role": "user", "content": prompt}]
        try:
            return await TAU.chat(mid, msgs, tg_id=chat_id)
        except Exception as ex:
            if TAU.is_exhausted(ex):
                return await TAU.chat(mid, msgs, proxy=PX.get_proxy(), tg_id=chat_id)
            raise
    async def _fn(key, h, m):
        return await F.chat(h, m, key=key)
    return await _alpha_silent(chat_id, _fn, history, mid)
async def translate(chat_id: int, ref: str, text: str, target_lang: str) -> str:
    prov, mid = parse(ref)
    if prov != PROV_DELTA:
        mid = "gpt-5-nano"
    async def _c(key, rec, px):
        return await DL.translate(key, text, target_lang, mid, proxy=px)
    return await _delta_call(chat_id, _c)
async def detect_lang(chat_id: int, ref: str, text: str) -> str:
    prov, mid = parse(ref)
    if prov != PROV_DELTA:
        mid = "gpt-5-nano"
    async def _c(key, rec, px):
        return await DL.detect_lang(key, text, mid, proxy=px)
    return await _delta_call(chat_id, _c)
async def image(chat_id: int, ref: str, prompt: str, image_url: str = None) -> dict:
    prov, mid = parse(ref)
    if prov == PROV_PI:
        url = await PI.image(mid, prompt, image_url=image_url)
        if not url:
            raise RuntimeError("pi image: ماكو رابط ناتج")
        return {"url": url}
    async def _fn(key, p):
        res = await F.image(p, model=mid, key=key)
        res = await F.job_result(res, key=key)
        url = res.get("url") or res.get("image_url") or res.get("output_url")
        if not url:
            raise RuntimeError("alpha image: ماكو رابط ناتج")
        return {"url": url, "share_url": res.get("share_url", "")}
    return await _alpha_silent(chat_id, _fn, prompt)
async def tts(chat_id: int, ref: str, text: str) -> dict:
    prov, mid = parse(ref)
    if prov == PROV_GTS:
        data = await GTS.synth(text)
        return {"bytes": data, "mime": "audio/mpeg"}
    async def _fn(key, t):
        res = await F.tts(t, model=mid, key=key)
        res = await F.job_result(res, key=key)
        url = res.get("url") or res.get("audio_url") or res.get("output_url")
        if not url:
            raise RuntimeError("alpha tts: ماكو رابط صوتي")
        return {"url": url}
    return await _alpha_silent(chat_id, _fn, text)
async def music(chat_id: int, ref: str, prompt: str) -> dict:
    prov, mid = parse(ref)
    async def _fn(key, p):
        res = await F.music(p, key=key)
        res = await F.job_result(res, timeout=CFG.MUSIC_TIMEOUT, key=key)
        url = res.get("url") or res.get("audio_url") or res.get("output_url")
        if not url:
            raise RuntimeError("alpha music: ماكو رابط صوتي")
        return {"url": url}
    return await _alpha_silent(chat_id, _fn, prompt)
