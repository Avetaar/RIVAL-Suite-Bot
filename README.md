<p align="center"><img src="RIVAL_banner.png" alt="RIVAL Suite Bot — Avetaar AI Suite" width="720"></p>

# RIVAL Suite Bot — Avetaar AI Suite
**الإصدار:** 0.1  •  **المطوّر:** Avetaar (@Avetaar)  •  **الفريق/الحقوق:** Rival

---

## العربية

بوت تلغرام يقوده الأزرار (لا أوامر نصية) يقدّم حزمة AI موحّدة: محادثة، صور، صوت، موسيقى، برمجة، ترجمة — عبر 9 موفّرين شغّالين مع حسابات تتدوّر تلقائياً لكل مستخدم.

### المميزات
- 💬 محادثة — نماذج GPT و Qwen و Llama موحّدة (509 نموذج)
- 🖼️ صورة — توليد وتعديل وإزالة خلفية
- 🔊 صوت — نص إلى صوت بالعربية
- 🎵 موسيقى — توليد موسيقي
- 🐍 برمجة — توليد كود وملفات جاهزة
- 🌐 ترجمة — 18 لغة بكشف تلقائي للغة المصدر
- ⚙️ **لوحة مطوّر** (خاصة بالمالك): فتح/إغلاق البوت للجميع، حظر/رفع أي مستخدم برقم أو من القائمة، مسح البيانات، إعادة إقلاع، فحص الموفّرين، إحصاءات
- 🔒 **حماية**: مستخدم محظور أو بوت مغلق → يرى رسالة + زر «اتصال بالمطور»
- 🎨 ألوان أزرار منسّقة: أزرق = خدمات/تنقل، أخضر = إيجابي، أحمر = خطر
- 🌐 **اتصال ذكي**: بروكسيات متجددة تلقائياً (26 مصدراً) مع حذف تلقائي للميت، وأولوية للمسار الموثّق
- 🔁 **تعافٍ ذاتي**: أي انقطاع أو 503/504/429 → تبديل مسار فوري + 4 محاولات
- 🚫 **قفل عملية واحدة** (Mutex على ويندوز / flock على لينكس) يمنع تعارض التوكن
- 🏃 يعمل على: Termux، لينكس، ماك، ويندوز، أي استضافة

### التثبيت والتشغيل — أمر واحد
**Termux / لينكس / ماك:**
```bash
./install.sh
```
**ويندوز:**
```bat
install.bat
```
المثبّت يثبّت الاعتماديات (httpx + Pillow)، ثم يسألك ثلاث أسئلة في التيرمينال:
1. توكن البوت (من @BotFather)
2. يوزر البوت بدون @ (لرابط اتصال بالمطور)
3. أيدي المالك الرقمي

بعد الإجابات يبدأ البوت فوراً. التوكن يُحفظ في `RIVAL/bot_credentials.json` (لا في الكود) — **لا ترفعه على جيت هب**.

### أوامر سريعة
```bash
# إيقاف
Ctrl+C

# تشغيل يدوي (بعد التثبيت)
python Avetaar.py

# متغيرات البيئة (بديل لملف الأمانات)
RIVAL_BOT_TOKEN=... RIVAL_OWNER_ID=... RIVAL_OWNER_USERNAME=... python Avetaar.py
```

### هيكل المشروع
```
Avetaar.py            نقطة الدخول (التوكن + أيدي المطور من الأمانات)
install.sh / .bat     مثبّت بامر واحد لكل المنصات
RIVAL/
├── RIVAL_config.py   إعدادات الموفّرين (روابط base64)
├── RIVAL_api.py      عميل API تلغرام (بروكسي + تعافٍ + إعادة محاولة)
├── RIVAL_unified.py  موحّد النماذج والتوجيه
├── RIVAL_handlers.py منطق الخدمات
├── RIVAL_dispatcher.py مسار الأزرار
├── RIVAL_devboard.py لوحة المطوّر
├── RIVAL_state.py    حفظ الحالة
├── RIVAL_proxies.py  حوض البروكسيات المتجدد
├── alpha..tau        موفّرون: alpha, gama, delta, eps, zeta, pi, gts, sig, tau
└── bot_credentials.json  (يولده المثبّت — خارج جيت)
```

### ملاحظات
- الروابط الأساسية للموفّرين مشفّرة base64 في `RIVAL_config.py`.
- الصور/الصوت تُنزل ثم تُرفع كملفات (مو روابط) للأمان.
- لوحة المطوّر تظهر للمالك فقط (أيدي من الأمانات).

---

## English

Button-driven Telegram bot (no text commands) exposing a unified AI suite: chat, image, TTS, music, coder, translate — across 9 live providers with per-user auto-rotating accounts.

### Features
- 💬 Chat — unified GPT / Qwen / Llama models (509 models)
- 🖼️ Image — generation, editing, background removal
- 🔊 TTS — text-to-speech in Arabic
- 🎵 Music — audio generation
- 🐍 Coder — code generation and ready-to-run files
- 🌐 Translate — 18 languages with automatic source detection
- ⚙️ **Dev Board** (owner only): open/close for everyone, ban/unban by ID or list, data purge, restart, provider probes, stats
- 🔒 **Safety**: banned user or closed bot → message + "Contact Dev" button
- 🎨 Consistent button colors: blue = services/nav, green = positive, red = danger
- 🌐 **Smart connectivity**: self-refreshing proxy pool (26 sources) with auto-purge of dead proxies, verified-route priority
- 🔁 **Self-healing**: any disconnect or 503/504/429 → instant route swap + 4 retries
- 🚫 **Single-instance lock** (Mutex on Windows / flock on Linux) prevents token conflicts
- 🏃 Runs on: Termux, Linux, macOS, Windows, any hosting

### Install & run — one command
**Termux / Linux / macOS:**
```bash
./install.sh
```
**Windows:**
```bat
install.bat
```
The installer installs dependencies (httpx + Pillow), then asks three questions in the terminal:
1. Bot token (from @BotFather)
2. Bot username without @ (for the dev contact link)
3. Owner's numeric Telegram ID

After answering, the bot starts immediately. The token is stored in `RIVAL/bot_credentials.json` (not in code) — **do not commit it to GitHub**.

### Quick commands
```bash
# stop
Ctrl+C

# manual run (after install)
python Avetaar.py

# env vars (alternative to the credentials file)
RIVAL_BOT_TOKEN=... RIVAL_OWNER_ID=... RIVAL_OWNER_USERNAME=... python Avetaar.py
```

### Project layout
```
Avetaar.py            entrypoint (token + owner id from credentials)
install.sh / .bat     one-command installer for all platforms
RIVAL/
├── RIVAL_config.py   provider config (base64 URLs)
├── RIVAL_api.py      Telegram API client (proxy + recovery + retry)
├── RIVAL_unified.py  unified models + routing
├── RIVAL_handlers.py service logic
├── RIVAL_dispatcher.py button routing
├── RIVAL_devboard.py owner dashboard
├── RIVAL_state.py    state persistence
├── RIVAL_proxies.py  self-refreshing proxy pool
├── alpha..tau        providers: alpha, gama, delta, eps, zeta, pi, gts, sig, tau
└── bot_credentials.json  (installer-generated — kept out of git)
```

### Notes
- Provider base URLs are base64-encoded in `RIVAL_config.py`.
- Images/audio are downloaded then re-uploaded as files (not links) for safety.
- The Dev Board is visible to the owner only (ID from credentials).

---

## GitHub / Channel description (bilingual)

**AR:**
```
RIVAL Suite Bot v0.1 — حزمة AI موحّدة بتلغرام: محادثة، صورة، صوت، موسيقى، برمجة، ترجمة عبر 9 موفّرين. زرّي بالكامل، لوحة مطوّر (فتح/إغلاق/حظر)، اتصال ذكي بتعافٍ ذاتي. يعمل على Termux/لينكس/ماك/ويندوز/استضافة.

⚡ أمر واحد للتثبيت: ./install.sh (أو install.bat)
🛠 المطوّر: Avetaar (@Avetaar) | فريق: Rival
```

**EN:**
```
RIVAL Suite Bot v0.1 — unified AI suite for Telegram: chat, image, TTS, music, coder, translate across 9 providers. Fully button-driven with an owner Dev Board (open/close/ban), smart connectivity and self-healing. Runs on Termux/Linux/macOS/Windows/hosting.

⚡ One-command install: ./install.sh (or install.bat)
🛠 Developer: Avetaar (@Avetaar) | Team: Rival
```
