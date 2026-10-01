import asyncio
import base64
import json
import os
import httpx
import RIVAL_config as CFG
API_BASE = CFG.PI_BASE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_KIND = {"flux-schnell": "gen", "gpt-image-2": "gen",
         "gpt-image-2-edit": "edit", "rembg": "bg", "bria-rmbg": "bg"}
_BLOCKED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "RIVAL_pi_blocked.json")
def _blocked():
    try:
        with open(_BLOCKED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()
def models_by_type(t):
    if t != "image":
        return []
    bl = _blocked()
    return [m for m in _KIND if m not in bl]
def display_label(mid):
    return mid
def kind_of(mid):
    return _KIND.get(mid)
def needs_image(mid):
    return _KIND.get(mid) in ("edit", "bg")
def needs_prompt(mid):
    return _KIND.get(mid) == "edit"
async def upload(image_data, proxy=None):
    if len(image_data) > 1024 * 1024:
        try:
            from io import BytesIO
            from PIL import Image
            im = Image.open(BytesIO(image_data))
            if im.mode == "RGBA":
                im = im.convert("RGB")
            im.thumbnail((1024, 1024))
            buf = BytesIO()
            im.save(buf, format="JPEG", quality=80, optimize=True)
            image_data = buf.getvalue()
        except Exception:
            pass
    b64 = base64.b64encode(image_data).decode()
    async with httpx.AsyncClient(proxy=proxy, timeout=40, verify=False,
                                 headers={"User-Agent": UA}) as c:
        r = await c.post(f"{API_BASE}/api/fal/upload",
                         json={"dataUrl": f"data:image/jpeg;base64,{b64}"})
    if r.status_code != 200:
        raise RuntimeError(f"pi upload HTTP {r.status_code}: {r.text[:200]}")
    url = r.json().get("url")
    if not url:
        raise RuntimeError("pi: ماكو رابط من رفع الصورة")
    return url
async def image(mid, prompt, image_url=None, proxy=None):
    kind = _KIND.get(mid)
    if not kind:
        raise RuntimeError(f"pic: النموذج {mid} غير معروف")
    payload = {"prompt": prompt, "image_size": "square_hd",
               "num_inference_steps": 8}
    if kind in ("edit", "bg"):
        if not image_url:
            raise RuntimeError("pic: هذا النموذج يحتاج صورة مرفوعة")
        payload["image_url"] = image_url
        if kind == "bg":
            payload["prompt"] = "remove background"
    async with httpx.AsyncClient(proxy=proxy, timeout=30, verify=False,
                                 headers={"User-Agent": UA}) as c:
        r = await c.post(f"{API_BASE}/api/fal/run",
                         json={"modelId": mid, "input": payload})
        if r.status_code != 200:
            raise RuntimeError(f"pic run HTTP {r.status_code}: {r.text[:200]}")
        jid = r.json().get("jobId")
        if not jid:
            raise RuntimeError(f"pic: ماكو jobId: {r.text[:200]}")
        last = {}
        for _ in range(60):
            await asyncio.sleep(3)
            ch = await c.get(f"{API_BASE}/api/fal/jobs/{jid}")
            if ch.status_code == 200:
                last = ch.json()
            st = last.get("status")
            if st == "succeeded":
                url = (last.get("outputs") or [{}])[0].get("url")
                if url:
                    return url
                raise RuntimeError("pic: job نجح بدون رابط")
            if st == "failed":
                raise RuntimeError(f"pic: job فشل: {json.dumps(last)[:200]}")
        raise RuntimeError(f"pic: job تأخر (تجاوز الوقت)")
