import httpx
import RIVAL_api as A
import RIVAL_alpha as F
import RIVAL_config as CFG
import RIVAL_keyboards as K
import RIVAL_state as S
import RIVAL_accounts as ACCT
import RIVAL_gamma_accounts as GAACCT
import RIVAL_delta_accounts as DLACCT
import RIVAL_pi as PI
import RIVAL_unified as U
import RIVAL_devboard as DEV
from RIVAL_emojis import EMO, esc
WELCOME = (EMO('crown') + " ✦ مساعد Avetaar ✦ " + EMO('sparkles')
           + "\nموفّرون موحّدون — اختر خدمة من الأزرار 👇")
CLOSED_MSG = (EMO('warning') + " 🔒 <b>البوت مغلق من قبل المطوّر</b> حالياً.\n"
              "اضغط الاتصال بالمطور لفتح البوت.")
BANNED_MSG = (EMO('cross') + " ⛔ <b>أنت محظور من استخدام البوت.</b>\n"
              "اضغط الاتصال بالمطور للتظلم.")
async def gate_reply(chat_id: int, status: str) -> None:
    if status == "closed":
        await A.message(chat_id, CLOSED_MSG, K.contact_dev_menu())
    elif status == "banned":
        await A.message(chat_id, BANNED_MSG, K.contact_dev_menu())
_CATS = ("chat", "image", "tts", "music", "coder")
def _err(ex: Exception, fallback: str) -> str:
    s = str(ex)
    if isinstance(ex, U.ServiceBusy):
        return EMO('warning') + " الخدمة مزدحمة هالشوي — جرب بعد دقيقة."
    low = s.lower()
    if any(t in low for t in ("connect", "proxy", "getaddrinfo", "timeout", "dns", "refused")):
        return EMO('warning') + " اتصال ضعيف هالحين — جرب ثانية بعد لحظات."
    if any(t in low for t in ("403", "429", "460", "human check", "requireshumancheck",
                               "forbidden", "rate limit", "too many requests",
                               "invalid response status")):
        return EMO('warning') + " الخدمة مزدحمة هالشوي — جرب بعد دقيقة."
    if "credits" in low or "balance" in low or "نفد" in s:
        print("[err] credit leak guarded:", s[:120])
        return EMO('warning') + " الخدمة مزدحمة — انتظر دقيقة ثم جرب ثانية."
    msg = fallback
    if s:
        msg += " (" + esc(s[:100]) + ")"
    return EMO('cross') + " " + msg
def _is_code_block(out: str) -> bool:
    if "```" in out:
        import re
        m = re.search(r"```(\w*)\n(.*?)```", out, re.DOTALL)
        if m and len(m.group(2)) > 400:
            return True
    lines = [l for l in out.splitlines() if l.strip()]
    if len(lines) >= 60:
        return True
    head = "\n".join(lines[:8])
    if "import " in head or "from " in head or "def " in head or "class " in head:
        return True
    return False
def _code_filename(out: str) -> str:
    import re
    m = re.search(r"```(\w+)", out)
    lang = (m.group(1).lower() if m else "")
    ext = {"python": "py", "py": "py", "javascript": "js", "js": "js",
           "java": "java", "typescript": "ts", "ts": "ts", "c": "c",
           "cpp": "cpp", "c++": "cpp", "rust": "rs", "go": "go",
           "html": "html", "css": "css", "json": "json", "bash": "sh",
           "sh": "sh", "shell": "sh", "php": "php", "ruby": "rb"}.get(lang, "txt")
    return "avetaar_" + ext if ext != "txt" else "avetaar_code"
def _ref(chat_id: int, cat: str) -> str:
    return S.model_for(chat_id, cat) or U.default_ref(cat)
async def _rotated_alpha(chat_id: int, fn, **kw):
    key = await ACCT.ensure_account(chat_id)
    try:
        return await fn(key=key, **kw)
    except Exception as ex:
        if ACCT.is_credit_error(ex):
            key = await ACCT.rotate(chat_id)
            return await fn(key=key, **kw)
        raise
async def on_new_user(chat_id: int) -> None:
    S.ensure(chat_id)
    S.clear_mode(chat_id)
    await A.message(chat_id, WELCOME, K.main_menu(chat_id))
async def on_text(chat_id: int, text: str) -> None:
    st = S.get(chat_id)
    mode = st.get("mode", None)
    if text.strip().lower() in ("/start", "/menu", "/main"):
        await on_new_user(chat_id)
        return
    if text.strip().lower() in ("/dev", "/status"):
        if not DEV.is_owner(chat_id):
            await A.message(chat_id, EMO('cross') + " هذه الأوامر للمطوّر فقط.",
                            K.main_menu(chat_id))
            return
        await on_new_user(chat_id)
        report = await DEV.full_report(chat_id)
        await A.message(chat_id, report, K.dev_menu())
        return
    dp = S.dev_pending(chat_id)
    if dp and DEV.is_owner(chat_id):
        d = text.strip()
        if d in ("❌", "إلغاء", "cancel", "back", "/cancel", "رجوع"):
            S.set_dev_pending(chat_id, None)
            await A.message(chat_id, EMO('check') + " أُلغي الطلب.", K.dev_menu())
            return
        if d.isdigit():
            S.set_dev_pending(chat_id, None)
            target = int(d)
            res = DEV.ban_user(target) if dp == "ban" else DEV.unban_user(target)
            await A.message(chat_id, EMO('check') + " " + res + "\n"
                            + DEV.banned_report(), K.dev_menu())
            return
        await A.message(chat_id, EMO('cross') + " أرسل رقم المعرف فقط (أرقام)\nأو ❌ للإلغاء",
                       K.dev_menu())
        return
    _img = S.get_image(chat_id)
    if _img:
        _ref0 = _ref(chat_id, "image")
        _p0, _m0 = U.parse(_ref0)
        if _p0 == U.PROV_PI and PI.needs_prompt(_m0):
            S.clear_image(chat_id)
            await _run_pi(chat_id, _ref0, _m0, _img, text.strip())
            return
    if mode == "chat":
        await do_chat(chat_id, text)
    elif mode == "image":
        await do_image(chat_id, text)
    elif mode == "tts":
        await do_tts(chat_id, text)
    elif mode == "music":
        await do_music(chat_id, text)
    elif mode == "coder":
        await do_coder(chat_id, text)
    elif mode == "translate":
        await do_translate(chat_id, text)
    else:
        await on_new_user(chat_id)
async def on_photo(chat_id: int, msg: dict) -> None:
    ref = _ref(chat_id, "image")
    prov, mid = U.parse(ref)
    if prov != U.PROV_PI or not PI.needs_image(mid):
        await A.message(chat_id,
                        EMO('cross') + " هذا النموذج يولّد من نص، مو من صورة.\n"
                        + "اختر نموذج تعديل/خلفية من زر «نماذج» ثم أرسل صورتك.",
                        K.image_menu())
        return
    data = None
    try:
        ph = (msg.get("photo") or [None])[-1]
        if ph:
            data = await A.get_file_bytes(ph["file_id"])
        else:
            doc = msg.get("document")
            if doc:
                data = await A.get_file_bytes(doc["file_id"])
    except Exception as ex:
        print("[photo-dl-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر تنزيل الصورة"),
                        K.image_menu())
        return
    if not data:
        await A.message(chat_id, EMO('cross') + " ما وصلت صورة", K.image_menu())
        return
    cap = msg.get("caption") or ""
    S.set_image(chat_id, data)
    if PI.needs_prompt(mid) and not cap.strip():
        await A.message(chat_id,
                        EMO('check') + " حفظت الصورة ✓ اكتب الآن وصف التعديل اللي تريده\n"
                        + "(سيرفعها مع الوصف تلقائيًا)", K.image_menu())
        return
    prompt = cap.strip() if PI.needs_prompt(mid) else "remove background"
    await _run_pi(chat_id, ref, mid, data, prompt)
async def _run_pi(chat_id: int, ref: str, mid: str, image_bytes: bytes,
                  prompt: str) -> None:
    a_id = await A.progress(chat_id, "image",
                             "✦ جاري رفع الصورة والتعديل — " + esc(mid) + "\n⏳ قد يأخذ دقيقة",
                             K.image_menu())
    try:
        up_url = await PI.upload(image_bytes)
        res = await U.image(chat_id, ref, prompt, image_url=up_url)
        url = res.get("url")
        if not url:
            raise RuntimeError("لا رابط ناتج")
        S.clear_image(chat_id)
        await A.delete(chat_id, a_id)
        await A.photo(chat_id, url,
                      EMO('trophy') + " ✦ تم " + ("تعديل" if PI.needs_prompt(mid)
                                                   else "إزالة الخلفية") + " ✓",
                      K.image_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[pi-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر تعديل الصورة"),
                        K.image_menu())
async def do_chat(chat_id: int, text: str) -> None:
    ref = _ref(chat_id, "chat")
    a_id = await A.progress(chat_id, "chat",
                             "✦ جاري كتابة الرد — " + esc(U.label_of(ref)),
                             K.chat_menu())
    try:
        hist = S.history(chat_id)
        hist.append({"role": "user", "content": text})
        reply = await U.chat(chat_id, ref, text, hist[-(CFG.CHAT_HISTORY_DEPTH + 1):])
        hist.append({"role": "assistant", "content": reply})
        S.set_history(chat_id, hist)
        S.set_mode(chat_id, "chat")
        await A.delete(chat_id, a_id)
        hdr = EMO('check') + " \u2726 <b>\u0627\u0644\u0631\u062f</b> (" + esc(U.label_of(ref)) + ")\n\n"
        msg = hdr + esc(reply, 3900)
        await A.message(chat_id, msg, K.chat_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[chat-err]", ex)
        await A.message(chat_id, _err(ex, "ماكو رد من النموذج هالحين"), K.chat_menu())
async def do_translate(chat_id: int, text: str) -> None:
    S.clear_mode(chat_id)
    ref = _ref(chat_id, "translate")
    lang = S.translate_lang(chat_id)
    a_id = await A.progress(chat_id, "translate",
                             "✦ جاري الترجمة — " + esc(U.label_of(ref)) + "\n⏳ كشف اللغة ثم التوليد",
                             K.translate_menu())
    try:
        src = await U.detect_lang(chat_id, ref, text)
        out = await U.translate(chat_id, ref, text, lang)
        await A.delete(chat_id, a_id)
        msg = (EMO('globe') + " ✦ <b>الترجمة</b> (" + esc(U.label_of(ref)) + ")\n"
               + EMO('arrow') + " الأصلية: " + esc(src, 6)
               + "  →  الهدف: " + esc(lang, 6) + "\n\n"
               + "<b>" + esc(out, 3900) + "</b>")
        await A.message(chat_id, msg, K.translate_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[translate-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر إتمام الترجمة"),
                        K.translate_menu())
async def do_image(chat_id: int, prompt: str) -> None:
    S.clear_mode(chat_id)
    ref = _ref(chat_id, "image")
    a_id = await A.progress(chat_id, "image",
                             "✦ جاري إنشاء الصورة — " + esc(U.label_of(ref)) + "\n⏳ وصفي «" + esc(prompt, 200) + "»",
                             K.image_menu())
    try:
        res = await U.image(chat_id, ref, prompt)
        if res.get("bytes"):
            await A.delete(chat_id, a_id)
            cap = EMO('picture') + " " + esc(prompt, 60)
            await A.photo_bytes(chat_id, res["bytes"], res.get("mime", "image/png"),
                                cap, K.image_menu())
            return
        url = res.get("url")
        if not url:
            raise RuntimeError("لا رابط ناتج في الاستجابة")
        await A.delete(chat_id, a_id)
        cap = EMO('picture') + " " + esc(prompt, 60)
        await A.photo(chat_id, url, cap, K.image_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[image-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر توليد الصورة"),
                        K.image_menu())
async def do_tts(chat_id: int, text: str) -> None:
    S.clear_mode(chat_id)
    ref = _ref(chat_id, "tts")
    a_id = await A.progress(chat_id, "tts",
                             "✦ جاري توليد الصوت — " + esc(U.label_of(ref)) + "\n⏳ قد يأخذ حتى دقيقة",
                             K.tts_menu())
    try:
        res = await U.tts(chat_id, ref, text)
        if res.get("bytes"):
            await A.delete(chat_id, a_id)
            await A.audio_bytes(chat_id, res["bytes"],
                                EMO('bell') + " ✦ " + esc(text, 80),
                                K.tts_menu(), as_voice=True,
                                mime=res.get("mime", "audio/mpeg"))
            return
        url = res.get("url")
        if not url:
            raise RuntimeError("لا رابط صوتي في الاستجابة")
        await A.delete(chat_id, a_id)
        await A.audio(chat_id, url, EMO('bell') + " ✦ " + esc(text, 80),
                      K.tts_menu(), as_voice=True)
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[tts-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر توليد الصوت"),
                        K.tts_menu())
async def do_music(chat_id: int, text: str) -> None:
    S.clear_mode(chat_id)
    ref = _ref(chat_id, "music")
    a_id = await A.progress(chat_id, "music",
                             "✦ جاري توليد الموسيقى — " + esc(U.label_of(ref)) + "\n⏳ قد يأخذ بضع دقائق",
                             K.music_menu())
    try:
        res = await U.music(chat_id, ref, text)
        url = res.get("url")
        if not url:
            raise RuntimeError("لا رابط صوتي في الاستجابة")
        await A.delete(chat_id, a_id)
        await A.audio(chat_id, url, EMO('fire') + " ✦ " + esc(text, 80), K.music_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[music-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر توليد الموسيقى"),
                        K.music_menu())
async def do_coder(chat_id: int, text: str) -> None:
    S.clear_mode(chat_id)
    ref = _ref(chat_id, "coder")
    prov, mid = U.parse(ref)
    if prov != U.PROV_FREE:
        mid = CFG.CODER_MODEL
    a_id = await A.progress(chat_id, "coder",
                             "✦ جاري التنفيذ والتفكير — " + esc(mid) + "\n⏳ قد يأخذ دقيقة",
                             K.coder_menu())
    try:
        out = (await _coder_run(chat_id, mid, text)).strip()
        await A.delete(chat_id, a_id)
        if not out:
            msg = EMO('warning') + " نفّذت العملية بدون إخراج."
            await A.message(chat_id, msg, K.coder_menu())
            return
        if _is_code_block(out):
            fname = _code_filename(out)
            await A.document(chat_id, out.encode("utf-8"), fname,
                             EMO('python') + " ✦ ملف جاهز للتشغيل (" + esc(fname) + ")",
                             K.coder_menu())
            return
        msg = EMO('check') + "\n" + esc(out, 3900)
        await A.message(chat_id, msg, K.coder_menu())
    except Exception as ex:
        await A.delete(chat_id, a_id)
        print("[coder-err]", ex)
        await A.message(chat_id, _err(ex, "تعذر تنفيذ العملية"),
                        K.coder_menu())
async def _coder_session(chat_id: int, model: str, key: str) -> str:
    st = S.get(chat_id)
    sid = st.get("coder_session")
    if not sid or st.get("coder_model") != model or st.get("coder_account") != key:
        res = await _rotated_alpha(chat_id, F.coder_session, model_id=model)
        sid = res.get("session_id") or res.get("id")
        if not sid:
            raise RuntimeError(f"لا جلسة في الرد: {str(res)[:120]}")
        S.set_coder_session(chat_id, sid)
        S.get(chat_id)["coder_model"] = model
        S.get(chat_id)["coder_account"] = key
        S._save(S.get(chat_id))
    return sid
async def _coder_run(chat_id: int, model: str, text: str) -> str:
    key = await ACCT.ensure_account(chat_id)
    sid = await _coder_session(chat_id, model, key)
    try:
        return await F.coder_message(sid, text, key=key)
    except Exception as ex:
        if ACCT.is_credit_error(ex):
            key = await ACCT.rotate(chat_id)
            sid = await _coder_session(chat_id, model, key)
            return await F.coder_message(sid, text, key=key)
        raise
def _cat_title(cat: str) -> str:
    for key, label, _ in K.CATEGORIES:
        if key == cat:
            return label
    return cat
async def show_model_page(chat_id: int, mid: int, cat: str, page: int) -> None:
    if cat not in _CATS:
        await A.edit(chat_id, mid, EMO('cross') + " قسم غير معروف", K.cats_page_kb(0))
        return
    try:
        entries = await U.unified_models(cat)
    except Exception as ex:
        print("[models-err]", ex)
        await A.edit(chat_id, mid, _err(ex, "تعذر جلب النماذج"), K.cats_page_kb(0))
        return
    labels = [lab for _, lab in entries]
    if not labels:
        await A.edit(chat_id, mid, "لا توجد نماذج في قسم " + cat, K.cats_page_kb(0))
        return
    refs = [r for r, _ in entries]
    cur = S.model_for(chat_id, cat) or U.default_ref(cat)
    cur_idx = refs.index(cur) if cur in refs else None
    kb = K.models_page_kb(cat, labels, page, cur_idx)
    await A.edit(chat_id, mid,
                 EMO('chart') + " ✦ نماذج «" + _cat_title(cat) + "» — "
                 + str(len(labels)) + "\nاضغط نموذجا لاعتماده", kb)
async def select_model(chat_id: int, mid: int, cat: str, idx: int) -> None:
    try:
        entries = await U.unified_models(cat)
        if idx >= len(entries):
            await A.edit(chat_id, mid, EMO('cross') + " فهرس خارج الحدود", K.cats_page_kb(0))
            return
        ref, label = entries[idx]
        S.set_model(chat_id, cat, ref)
        if cat == "coder":
            st = S.get(chat_id)
            st["coder_model"] = None
            st["coder_account"] = None
            S._save(st)
        await A.edit(chat_id, mid,
                     EMO('trophy') + " ✦ أعتُمِد: " + esc(label, 80)
                     + "\nاضغط خدمة للاستخدام", K.cats_page_kb(0))
    except Exception as ex:
        await A.edit(chat_id, mid, EMO('cross') + " " + esc(ex, 120), K.cats_page_kb(0))
