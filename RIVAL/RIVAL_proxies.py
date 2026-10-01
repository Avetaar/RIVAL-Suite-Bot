import json
import os
import re
import time
import random
import httpx
import concurrent.futures
import RIVAL_config as CFG
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
FPL_URL = "https://free-proxy-list.net/"
VERX1_API = "https://api.verx1.xyz/social/api.php?action=list"
VERIFY_URL = "https://api.ipify.org"
SCRAPER_URLS = [
    "http://alexa.lr2b.com/proxylist.txt",
    "https://www.us-proxy.org/",
    "https://spys.one/proxy-list/country/us/",
    "http://proxydb.net/",
    "http://olaf4snow.com/public/proxy.txt",
    "http://westdollar.narod.ru/proxy.htm",
    "http://tomoney.narod.ru/help/proxi.htm",
    "http://sergei-m.narod.ru/proxy.htm",
    "http://rammstein.narod.ru/proxy.html",
    "http://inav.chat.ru/ftp/proxy.txt",
    "http://johnstudio0.tripod.com/index1.htm",
    "http://hack-hack.chat.ru/proxy/allproxy.txt",
    "http://hack-hack.chat.ru/proxy/anon.txt",
    "http://hack-hack.chat.ru/proxy/p1.txt",
    "http://hack-hack.chat.ru/proxy/p2.txt",
    "http://hack-hack.chat.ru/proxy/p3.txt",
    "http://hack-hack.chat.ru/proxy/p4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
]
_HERE = os.path.dirname(os.path.abspath(__file__))
_POOL_FILE = os.path.join(_HERE, "proxies_pool.json")
_VERIFIED_FILE = os.path.join(_HERE, "verified_proxies.json")
PREFERRED = [
    "https://:9f43885a4284fba7780fb0554073c9e1@falunian.galactose.malaxation.melanterite.subtenant.popochek.com:25936",
]
_POOL: list = []
_VERIFIED: list = []
_FRESH_AT: float = 0.0
def _scrape_fpl() -> list:
    try:
        r = httpx.get(FPL_URL, timeout=30, headers={"User-Agent": UA})
        out = []
        for m in re.finditer(
            r"<tr>\s*<td>(\d+\.\d+\.\d+\.\d+)</td>\s*<td>(\d+)</td>(.*?)</tr>",
            r.text, re.S):
            ip, port, block = m.group(1), m.group(2), m.group(3)
            https = re.search(r"<td class='hx'>(yes|no)</td>", block)
            scheme = "https" if (https and https.group(1) == "yes") else "http"
            out.append(f"{scheme}://{ip}:{port}")
        return out
    except Exception:
        return []
def _scrape_verx1() -> list:
    try:
        r = httpx.get(VERX1_API, timeout=CFG.PROXY_FETCH_TIMEOUT,
                      headers={"User-Agent": UA})
        data = r.json()
        return [p["proxy"] for p in data.get("proxies", []) if p.get("proxy")]
    except Exception:
        return []
_IP_RE = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
def _scrape_generic(url: str, scheme: str = "http") -> list:
    out = []
    try:
        r = httpx.get(url, timeout=CFG.PROXY_FETCH_TIMEOUT,
                      headers={"User-Agent": UA}, follow_redirects=True)
        body = r.text
        if "list" in url.lower() or url.endswith(".txt"):
            for line in body.splitlines():
                line = line.strip().replace(",", " ")
                parts = line.split()
                host = parts[0]
                if not re.match(_IP_RE, host):
                    continue
                m = re.match(_IP_RE + r":(\d+)$", host)
                if m:
                    out.append(f"{scheme}://{host}")
                elif len(parts) > 1 and re.match(_IP_RE + r":(\d+)", host):
                    continue
                elif len(parts) > 1:
                    port = parts[1]
                    if port.isdigit() and int(port) <= 65535:
                        out.append(f"{scheme}://{host}:{port}")
        else:
            for m in re.finditer(_IP_RE + r"\s*<[^>]*>\s*(?:\n\s*)?(\d+)", body):
                out.append(f"{scheme}://{m.group(1)}:{m.group(2)}")
            for m in re.finditer(r"<td>(\d+\.\d+\.\d+\.\d+)</td>\s*<td>(\d+)</td>", body):
                out.append(f"{scheme}://{m.group(1)}:{m.group(2)}")
            for m in re.finditer(r"(?:http|https)://(\d+\.\d+\.\d+\.\d+:\d+)", body):
                out.append("http://" + m.group(1))
    except Exception:
        return []
    return out
def _scrape_all() -> list:
    cands = _scrape_fpl() + _scrape_verx1()
    for u in SCRAPER_URLS:
        low = u.lower()
        sch = "http"
        if "socks5" in low:
            sch = "socks5"
        elif "socks4" in low:
            sch = "socks4"
        cands.extend(_scrape_generic(u, sch))
    return cands
def _verify_one(px: str, timeout: int = 8) -> bool:
    try:
        with httpx.Client(proxy=px, timeout=timeout) as c:
            r = c.get(VERIFY_URL, headers={"User-Agent": UA}, follow_redirects=True)
            return r.status_code == 200
    except Exception:
        return False
def _load_files() -> None:
    global _POOL, _VERIFIED, _FRESH_AT
    try:
        with open(_POOL_FILE, encoding="utf-8") as f:
            d = json.load(f)
        _POOL = [p for p in d.get("proxies", []) if isinstance(p, str)]
        _FRESH_AT = d.get("fetched_at", 0.0)
    except Exception:
        _POOL, _FRESH_AT = [], 0.0
    try:
        with open(_VERIFIED_FILE, encoding="utf-8") as f:
            v = json.load(f)
        _VERIFIED = [p for p in v if isinstance(p, str)]
    except Exception:
        _VERIFIED = []
    print(f"[proxies] loaded {len(_POOL)} pool / {len(_VERIFIED)} verified")
def _save_files() -> None:
    global _POOL, _VERIFIED
    with open(_POOL_FILE, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.time(),
                   "source": "free-proxy-list.net + verx1 (verified)",
                   "proxies": _POOL}, f, ensure_ascii=False, indent=1)
    with open(_VERIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(_VERIFIED, f, ensure_ascii=False, indent=1)
    print(f"[proxies] saved {len(_POOL)} pool / {len(_VERIFIED)} verified")
_load_files()
def update(force: bool = False, cap: int = 600) -> int:
    global _POOL, _VERIFIED, _FRESH_AT
    age = time.time() - _FRESH_AT
    if not force and age < CFG.PROXY_TTL and _POOL:
        return len(_POOL)
    candidates = _scrape_all()
    for p in PREFERRED:
        if p not in candidates:
            candidates.insert(0, p)
    seen, uniq = set(), []
    for p in candidates:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    uniq = uniq[:cap]
    for p in PREFERRED:
        if p not in uniq:
            uniq.insert(0, p)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        results = dict(zip(uniq, ex.map(_verify_one, uniq)))
    ok = [p for p in uniq if results.get(p)]
    old = [p for p in _POOL if p not in seen]
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        old_results = dict(zip(old, ex.map(_verify_one, old)))
    ok_old = [p for p in old if old_results.get(p)]
    _VERIFIED = list(dict.fromkeys(ok + ok_old))
    _POOL = list(dict.fromkeys(_VERIFIED))
    _FRESH_AT = time.time()
    _save_files()
    print(f"[proxies] refresh: {len(uniq)} new + {len(old)} old → "
          f"{len(_POOL)} live kept, {len(uniq) - len(ok) + len(old) - len(ok_old)} dead purged")
    return len(_POOL)
def get_proxy() -> str | None:
    pool = _VERIFIED or _POOL
    if not pool:
        return None
    return random.choice(pool)
def get_proxies(need: int = 4) -> list:
    out, seen = [], set()
    for p in (_VERIFIED or []):
        if p not in seen:
            seen.add(p); out.append(p)
        if len(out) >= need:
            return out
    rest = [p for p in dict.fromkeys(_POOL) if p not in seen]
    random.shuffle(rest)
    for p in rest:
        out.append(p)
        if len(out) >= need:
            break
    return out
def reachable(px: str) -> bool:
    return _verify_one(px, timeout=10)
def verified_count() -> int:
    return len(_VERIFIED)
def pool_size() -> int:
    return len(_POOL)
