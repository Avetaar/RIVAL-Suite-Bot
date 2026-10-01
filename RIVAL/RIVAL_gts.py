import base64
import httpx
import RIVAL_config as CFG
def models_by_type(t):
    return ["ar-XA"] if t == "tts" else []
def display_label(mid):
    return mid
async def synth(text, language="ar-XA", proxy=None):
    payload = {
        "audioConfig": {"audioEncoding": "MP3", "pitch": 0.0,
                        "speakingRate": 1.0, "volumeGainDb": 0.0},
        "input": {"text": text},
        "voice": {"languageCode": language,
                  "name": f"{language}-Standard-C", "ssmlGender": "MALE"},
    }
    async with httpx.AsyncClient(proxy=proxy, timeout=CFG.GTTS_TIMEOUT,
                                 verify=False) as c:
        r = await c.post(CFG.GTTS_URL, json=payload,
                         headers={"x-goog-api-key": CFG.GTTS_KEY,
                                  "content-type": "application/json"})
    if r.status_code != 200:
        raise RuntimeError(f"gts HTTP {r.status_code}: {r.text[:200]}")
    data = base64.b64decode(r.json().get("audioContent") or "")
    if not data:
        raise RuntimeError("gts: ماكو صوت في الرد")
    return data
