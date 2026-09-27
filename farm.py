#!/usr/bin/env python3
import os
import sys
import re
import json
import time
import random
import signal
import hashlib
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from telethon import TelegramClient, functions, types
    from telethon.errors import SessionPasswordNeededError
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False


# ============================================================
#   KONFIG — akan di-prompt manual di terminal
# ============================================================
API_ID = None
API_HASH = None
PHONE = None
BOT_USERNAME = "FarmBuddiesBot"

SESSION_NAME = "farm_session"
INIT_FILE = Path(__file__).resolve().parent / "init_data.txt"

BASE = "https://farm-buddies-api.htmmo2025.workers.dev/api"
SITE_ORIGIN = "https://farm-buddies.pages.dev"

FP = None
DEVICE_ID = None

TASK_IDS = [2, 3, 7]
SLOTS_PER = 20
AD_DWELL = 10.0
RELOGIN_EVERY = 40
MAX_ROUNDS = 500
TICK_MIN = 5.0
TICK_MAX = 60.0


# ============================================================
#   CLASS C — WARNA (LENGKAP dengan WHT)
# ============================================================
class C:
    RST = "\033[0m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GRN = "\033[32m"
    YEL = "\033[33m"
    BLU = "\033[34m"
    MAG = "\033[35m"
    CYN = "\033[36m"
    WHT = "\033[37m"
    GRY = "\033[90m"
    BGRN = "\033[92m"
    BYEL = "\033[93m"
    BBLU = "\033[94m"
    BMAG = "\033[95m"
    BCYN = "\033[96m"
    BOLD = "\033[1m"


def _init_ansi():
    if os.name == "nt":
        try:
            os.system("")
        except Exception:
            pass


_init_ansi()


def ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def tag(t):
    return f"{C.GRY}[{ts()}]{C.RST}"


def log(t, msg, color=None):
    if color is None:
        color = C.RST
    print(f"{tag(t)} {color}{msg}{C.RST}")
    sys.stdout.flush()


def human_secs(s):
    s = int(max(0, s))
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def banner():
    print()
    print(C.GRN + C.BOLD + "  ╔═══════════════════════════════════════════════════╗" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "  " + C.BYEL + C.BOLD + "BY @ : Samdeck" + C.RST + "                                     " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ╠═══════════════════════════════════════════════════╣" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "                                                   " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "          " + C.BMAG + C.BOLD + "🌾  F A R M   B U D D I E S  🌾" + C.RST + "              " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "          " + C.BCYN + "All-In-One Bot  v2.0" + C.RST + "                 " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "          " + C.DIM + "Farming + Ads Auto" + C.RST + "                   " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ║" + C.RST + "                                                   " + C.GRN + C.BOLD + "║" + C.RST)
    print(C.GRN + C.BOLD + "  ╚═══════════════════════════════════════════════════╝" + C.RST)
    print()


# ============================================================
#   GLOBALS
# ============================================================
G = {
    "STOP": False,
    "TG_CLIENT": None,
    "TOKEN": None,
    "DEVICE_ID": DEVICE_ID,
    "LAST_LOGIN": 0,
    "ADS_DONE": 0,
    "TOTAL_REWARD": 0,
    "PROFILE": None,
}


USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 16; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.7977.88 Safari/537.36 "
    "Telegram-Android/12.6.4 (Samsung SM-X110; Android 16; SDK 36; AVERAGE)"
)

HEADERS_BASE = {
    "content-type": "application/json",
    "origin": SITE_ORIGIN,
    "referer": SITE_ORIGIN + "/",
    "x-requested-with": "org.telegram.messenger.web",
    "accept": "*/*",
    "accept-language": "en,en-IN;q=0.9,en-US;q=0.8",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Android"',
    "user-agent": USER_AGENT,
}


# ============================================================
#   PROMPT LOGIN CONFIG
# ============================================================
def prompt_login_config():
    """Minta API_ID, API_HASH, PHONE manual di terminal"""
    global API_ID, API_HASH, PHONE

    print()
    print(C.CYN + "═" * 62 + C.RST)
    print(C.CYN + C.BOLD + "  🔐 LOGIN CONFIG — INPUT MANUAL" + C.RST)
    print(C.CYN + "═" * 62 + C.RST)
    print(C.YEL + "  Ambil API_ID & API_HASH dari:" + C.RST)
    print(C.YEL + "    https://my.telegram.org/apps" + C.RST)
    print()

    # API_ID
    while True:
        try:
            v = input(f"{C.WHT}  📝 API_ID (angka): {C.RST}").strip()
            if not v:
                print(f"{C.RED}  Kosong! Coba lagi.{C.RST}")
                continue
            if not v.isdigit():
                print(f"{C.RED}  Harus angka!{C.RST}")
                continue
            API_ID = int(v)
            break
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

    # API_HASH
    while True:
        try:
            v = input(f"{C.WHT}  📝 API_HASH: {C.RST}").strip()
            if not v:
                print(f"{C.RED}  Kosong! Coba lagi.{C.RST}")
                continue
            if len(v) < 20:
                print(f"{C.RED}  Minimal 20 karakter!{C.RST}")
                continue
            API_HASH = v
            break
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

    # PHONE
    while True:
        try:
            v = input(f"{C.WHT}  📝 Nomor HP (+62...): {C.RST}").strip()
            if not v:
                print(f"{C.RED}  Kosong! Coba lagi.{C.RST}")
                continue
            if not v.startswith("+"):
                v = "+" + v
            PHONE = v
            break
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

    print()
    print(C.BGRN + "  ✅ Config diterima:" + C.RST)
    print(f"     API_ID  : {C.CYN}{API_ID}{C.RST}")
    print(f"     API_HASH: {C.CYN}{API_HASH[:8]}...{C.RST}")
    print(f"     PHONE   : {C.CYN}{PHONE}{C.RST}")
    print()


# ============================================================
#   TELETHON LOGIN
# ============================================================
async def telethon_login():
    """Login Telethon dengan config dari terminal"""
    if not HAS_TELETHON:
        log("err", "Telethon tidak terinstall. pip install telethon", C.RED)
        return False

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        if PHONE:
            await client.start(phone=PHONE)
        else:
            await client.start()
    except SessionPasswordNeededError:
        pw = input(f"{C.WHT}🔐 Password 2FA: {C.RST}")
        await client.sign_in(password=pw)
    except Exception as e:
        log("err", f"Telethon login gagal: {e}", C.RED)
        return False

    if not await client.is_user_authorized():
        log("err", "Telethon belum login", C.RED)
        return False

    me = await client.get_me()
    log("tg", f"Login OK — {me.first_name} (@{me.username})", C.BGRN)

    G["TG_CLIENT"] = client
    return True


async def telethon_fetch_init_data():
    client = G["TG_CLIENT"]
    if not client:
        return None

    log("tg", "Ambil fresh initData...", C.BCYN)

    try:
        bot = await client.get_input_entity(BOT_USERNAME)

        full = await client(functions.users.GetFullUserRequest(id=bot))
        bot_info = getattr(full.full_user, "bot_info", None)

        target_url = None
        if bot_info and bot_info.menu_button:
            if hasattr(bot_info.menu_button, "url"):
                target_url = bot_info.menu_button.url
                log("tg", f"Menu URL: {target_url}", C.DIM)

        if not target_url:
            target_url = "https://farm-buddies.pages.dev/"
            log("tg", "Pakai fallback URL", C.YEL)

        result = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            from_bot_menu=True,
            url=target_url,
        ))

        parsed = urlparse(result.url)
        fragment = parsed.fragment or ""
        query = dict(parse_qsl(fragment))
        init_data = query.get("tgWebAppData")

        if not init_data:
            log("tg", "tgWebAppData tidak ada di URL", C.RED)
            return None

        init_data = unquote(init_data)

        try:
            INIT_FILE.write_text(init_data)
        except Exception:
            pass

        log("tg", f"initData OK ({len(init_data)} char)", C.BGRN)
        return init_data

    except Exception as e:
        log("tg", f"Fetch initData error: {e}", C.RED)
        return None


# ============================================================
#   FARM CLIENT
# ============================================================
class Farm:
    def __init__(self):
        self.s = requests.Session()
        self.token = None
        self.device_id = G["DEVICE_ID"]
        self.last_login = 0.0
        self.ads_done = 0
        self.total_reward = 0

    def _headers(self, auth=True):
        h = dict(HEADERS_BASE)
        h["x-farm-fp"] = FP
        if auth and self.token:
            h["authorization"] = f"Bearer {self.token}"
        return h

    async def login_async(self):
        init_data = await telethon_fetch_init_data()
        if not init_data:
            return False

        body = {
            "initData": init_data,
            "deviceId": self.device_id,
            "fingerprint": FP,
        }

        r = self.s.post(f"{BASE}/auth/telegram",
                        headers=self._headers(auth=False),
                        json=body, timeout=20)

        if not r.ok:
            log("auth", f"HTTP {r.status_code}: {r.text[:200]}", C.RED)
            return False

        d = r.json()
        self.token = d.get("token")
        if d.get("deviceId"):
            self.device_id = d["deviceId"]

        if not self.token:
            log("auth", f"No token: {json.dumps(d)[:200]}", C.RED)
            return False

        self.last_login = time.time()
        G["TOKEN"] = self.token
        G["PROFILE"] = d.get("profile") or {}
        log("auth", f"Login OK — @{G['PROFILE'].get('username', '?')}", C.BGRN)
        return True

    def ensure_fresh(self):
        if not self.token or (time.time() - self.last_login) > RELOGIN_EVERY:
            return self._sync_login()

    def _sync_login(self):
        if not INIT_FILE.exists():
            log("auth", "init_data.txt tidak ada", C.RED)
            return False

        init_data = INIT_FILE.read_text().strip()
        body = {
            "initData": init_data,
            "deviceId": self.device_id,
            "fingerprint": FP,
        }

        try:
            r = self.s.post(f"{BASE}/auth/telegram",
                            headers=self._headers(auth=False),
                            json=body, timeout=20)
            if r.ok:
                d = r.json()
                self.token = d.get("token")
                if d.get("deviceId"):
                    self.device_id = d["deviceId"]
                self.last_login = time.time()
                G["TOKEN"] = self.token
                G["PROFILE"] = d.get("profile") or {}
                return bool(self.token)
        except Exception as e:
            log("auth", f"Sync login error: {e}", C.RED)

        return False

    def _retry_auth(self, fn):
        r = fn()
        if r.status_code in (401, 403):
            self._sync_login()
            r = fn()
        return r

    def get(self, path, **kw):
        self.ensure_fresh()
        return self._retry_auth(
            lambda: self.s.get(f"{BASE}{path}", headers=self._headers(),
                                timeout=20, **kw)
        )

    def post(self, path, body=None):
        self.ensure_fresh()
        return self._retry_auth(
            lambda: self.s.post(f"{BASE}{path}", headers=self._headers(),
                                 json=body if body is not None else {},
                                 timeout=20)
        )

    def farm(self):
        return self.get("/farm").json()

    def plant(self, idx, crop):
        return self.post("/farm/plant", {"idx": idx, "crop": crop})

    def water(self, idx):
        return self.post("/farm/water", {"idx": idx})

    def farm_ad_session(self, ref):
        return self.post("/ads/farm/session", {"ref": ref})

    def farm_ad_complete(self, sid, ref, provider, cr):
        return self.post("/ads/farm/complete", {
            "sessionId": sid, "ref": ref, "provider": provider,
            "clicked": True, "adsgramClicked": bool(cr),
        })

    def harvest_ad_session(self, idx):
        return self.post("/ads/harvest/session", {"idx": idx})

    def harvest_ad_complete(self, sid, provider, cr):
        return self.post("/ads/harvest/complete", {
            "sessionId": sid, "provider": provider,
            "clicked": True, "adsgramClicked": bool(cr),
        })

    def open_session(self, task_id, slot_index=-1):
        return self.post(f"/ads/task/{task_id}/session",
                          {"slotIndex": slot_index})

    def complete(self, task_id, slot_index, session_id, provider, cr):
        body = {
            "sessionId": session_id,
            "slotIndex": slot_index,
            "provider": provider,
            "clicked": True,
        }
        if cr:
            body["adsgramClicked"] = True
        return self.post(f"/ads/task/{task_id}/complete", body)


# ============================================================
#   HELPERS
# ============================================================
def plot_by_idx(state, idx):
    for p in (state.get("farm") or {}).get("plots", []):
        if p["idx"] == idx:
            return p
    return None


def short_err(resp):
    try:
        d = resp.json()
        code = d.get("code") or d.get("error") or "?"
        msg = d.get("message") or d.get("detail") or ""
        return f"{code}{(' · ' + msg) if msg else ''}"
    except Exception:
        return resp.text[:80].replace("\n", " ")


def parse_cooldown(d):
    for k in ("availableAt", "retryAfter", "nextAvailableAt"):
        if k in d:
            v = d[k]
            if isinstance(v, (int, float)):
                if v > 1e12:
                    return max(0.0, v / 1000.0 - time.time())
                if v > 1e9:
                    return max(0.0, float(v) - time.time())
                return max(0.0, float(v))
    return 0.0


def parse_available_at(resp):
    try:
        return parse_cooldown(resp.json())
    except Exception:
        return 0.0


def ad_dwell(session):
    mw = float(session.get("minWatchSec") or 0)
    exp = session.get("expiresAt", 0)
    ttl = (exp / 1000) - time.time() if exp else 999.0
    return min(max(AD_DWELL, mw + 1.5), max(2.0, ttl - 5))


# ============================================================
#   ADS LOGIC
# ============================================================
def watch_ads_task(f, task_id, slot_index=-1):
    r = f.open_session(task_id, slot_index)
    if r.status_code in (401, 403):
        f._sync_login()
        r = f.open_session(task_id, slot_index)

    if not r.ok:
        if r.status_code in (409, 429):
            cd = parse_available_at(r)
            return None, cd if cd > 0 else 30.0
        log(f"t{task_id}", f"Session {r.status_code}: {short_err(r)}", C.RED)
        return None, None

    s = r.json()
    sid = s.get("sessionId")
    if not sid:
        log(f"t{task_id}", "No sessionId", C.RED)
        return None, None

    prov = s.get("provider", "adsgram")
    cr = bool(s.get("clickRequired"))
    wait = ad_dwell(s)
    slot = s.get("slotIndex", "?")

    log(f"t{task_id}", f"Watch slot={slot} prov={prov} wait={wait:.1f}s", C.BCYN)
    time.sleep(wait)

    rr = f.complete(task_id, slot_index, sid, prov, cr)
    if rr.status_code in (401, 403):
        f._sync_login()
        rr = f.complete(task_id, slot_index, sid, prov, cr)

    if not rr.ok:
        log(f"t{task_id}", f"Complete {rr.status_code}: {short_err(rr)}", C.RED)
        return None, None

    d = rr.json()
    reward = d.get("reward", 0)
    f.ads_done += 1
    f.total_reward += reward
    log(f"t{task_id}", f"+{reward} coins (total={f.total_reward})", C.BGRN)
    return d, None


def pick_crop(farm_state):
    level = farm_state.get("farmLevel", 1)
    max_same = farm_state.get("maxSameCrop", 1)
    in_use = {}
    for p in farm_state.get("plots", []):
        if p.get("state") in ("growing", "ready") and p.get("crop"):
            in_use[p["crop"]] = in_use.get(p["crop"], 0) + 1

    choices = []
    for c in farm_state.get("crops", []):
        if c.get("locked"):
            continue
        if c.get("minFarmLevel", 1) > level:
            continue
        if c.get("leftToday", 0) <= 0:
            continue
        if max_same > 0 and in_use.get(c["id"], 0) >= max_same:
            continue
        choices.append(c)

    if not choices:
        return None
    choices.sort(key=lambda c: c.get("payout", 0), reverse=True)
    return choices[0]["id"]


def watch_water_ad(f):
    r = f.farm_ad_session("water")
    if not r.ok:
        if r.status_code in (409, 429):
            cd = parse_available_at(r)
            log("wtr", f"Cool {human_secs(cd)}", C.YEL)
        else:
            log("wtr", f"Session {r.status_code}: {short_err(r)}", C.RED)
        return None

    s = r.json()
    sid = s.get("sessionId")
    if not sid:
        log("wtr", "No sessionId", C.RED)
        return None

    prov = s.get("provider", "adsgram")
    cr = bool(s.get("clickRequired"))
    wait = ad_dwell(s)
    log("wtr", f"Watch ad wait={wait:.1f}s", C.BCYN)
    time.sleep(wait)

    rr = f.farm_ad_complete(sid, "water", prov, cr)
    if not rr.ok:
        log("wtr", f"Complete {rr.status_code}: {short_err(rr)}", C.RED)
        return None

    d = rr.json()
    farm_after = d.get("farm") or {}
    log("wtr", f"Refilled water={farm_after.get('water')}/{farm_after.get('waterMax')}", C.BGRN)
    return d


def watch_harvest_ad(f, idx):
    r = f.harvest_ad_session(idx)
    if not r.ok:
        if r.status_code in (409, 429):
            cd = parse_available_at(r)
            log(f"h{idx}", f"Cool {human_secs(cd)}", C.YEL)
            return {"_status": r.status_code, "_cooldown": cd}
        log(f"h{idx}", f"Session {r.status_code}: {short_err(r)}", C.RED)
        return {"_status": r.status_code, "_cooldown": 0}

    s = r.json()
    sid = s.get("sessionId")
    if not sid:
        return None

    prov = s.get("provider", "adsgram")
    cr = bool(s.get("clickRequired"))
    wait = ad_dwell(s)
    log(f"h{idx}", f"Watch ad wait={wait:.1f}s", C.BCYN)
    time.sleep(wait)

    rr = f.harvest_ad_complete(sid, prov, cr)
    if not rr.ok:
        log(f"h{idx}", f"Complete {rr.status_code}: {short_err(rr)}", C.RED)
        return None

    d = rr.json()
    h = d.get("harvested") or {}
    if h.get("ok"):
        coins = h.get("coins", 0)
        log(f"h{idx}", f"Harvested +{coins} coins", C.BGRN)
    return d


# ============================================================
#   PHASE FUNCTIONS
# ============================================================
def phase_harvest(f, state):
    ready = [p for p in (state.get("farm") or {}).get("plots", [])
             if p.get("state") == "ready"]

    if not ready:
        return False, 0.0

    attempted = False
    next_wait = 0.0

    for p in ready:
        idx = p["idx"]
        need = int(p.get("adsNeeded") or 1)
        done = int(p.get("adsDone") or 0)
        crop = p.get("crop")

        log("frm", f"Ready idx={idx} {crop} ads={done}/{need}", C.BMAG)

        d = watch_harvest_ad(f, idx)
        attempted = True

        if d is None:
            next_wait = max(next_wait, 30.0)
            continue

        if "_status" in d and d["_status"] in (409, 429):
            next_wait = max(next_wait, (d.get("_cooldown") or 30.0) + 2.0)
            continue

        if "farm" in d:
            state["farm"] = d["farm"]
        if "profile" in d:
            state["profile"] = d["profile"]

    return attempted, next_wait


def phase_plant(f, state):
    farm = state.get("farm") or {}
    did = False
    for p in farm.get("plots", []):
        if p.get("locked") or p.get("state") != "empty":
            continue
        crop = pick_crop(farm)
        if not crop:
            break
        r = f.plant(p["idx"], crop)
        if r.ok:
            did = True
            d = r.json()
            if "farm" in d:
                state["farm"] = d["farm"]
                farm = state["farm"]
            log("frm", f"Planted idx={p['idx']} {crop}", C.BBLU)
        else:
            log("frm", f"Plant err: {short_err(r)}", C.RED)
    return did


def phase_water(f, state):
    did = False
    farm = state.get("farm") or {}
    for p in farm.get("plots", []):
        if p.get("state") != "growing" or p.get("watered"):
            continue

        water = farm.get("water", 0)
        cost = farm.get("waterCost", 10)

        if water < cost:
            log("frm", f"Water low {water}/{farm.get('waterMax')} — ad refill", C.YEL)
            d = watch_water_ad(f)
            if d is None:
                break
            if "farm" in d:
                state["farm"] = d["farm"]
                farm = state["farm"]
                water = farm.get("water", 0)
                cost = farm.get("waterCost", 10)
            if water < cost:
                break

        r = f.water(p["idx"])
        if r.ok:
            did = True
            d = r.json()
            if "farm" in d:
                state["farm"] = d["farm"]
                farm = state["farm"]
            log("frm", f"Watered idx={p['idx']}", C.BCYN)
        else:
            log("frm", f"Water err: {short_err(r)}", C.RED)
    return did


def run_ads_round(f):
    done_per_task = {tid: 0 for tid in TASK_IDS}
    cooldown_until = {tid: 0.0 for tid in TASK_IDS}
    round_n = 0

    while round_n < MAX_ROUNDS:
        if G["STOP"]:
            break
        round_n += 1
        any_attempted = False

        for tid in TASK_IDS:
            if G["STOP"]:
                break
            if done_per_task[tid] >= SLOTS_PER:
                continue
            if time.time() < cooldown_until[tid]:
                continue

            any_attempted = True
            _, cd = watch_ads_task(f, tid, -1)

            if cd:
                backoff = min(cd, 300)
                cooldown_until[tid] = time.time() + backoff
                log(f"t{tid}", f"Cool {human_secs(backoff)}", C.YEL)
            else:
                done_per_task[tid] += 1
                time.sleep(2.0)

            if RELOGIN_EVERY and f.ads_done and f.ads_done % RELOGIN_EVERY == 0:
                f._sync_login()

        if not any_attempted:
            soonest = min(
                (cooldown_until[tid] for tid in TASK_IDS
                 if done_per_task[tid] < SLOTS_PER),
                default=None,
            )
            if soonest is None:
                break
            wait = max(2.0, soonest - time.time())
            if wait > 300:
                log("idle", f"All cooling — stop ads loop", C.YEL)
                break
            time.sleep(wait)
            continue

        prog = " · ".join(f"t{tid}:{done_per_task[tid]}" for tid in TASK_IDS)
        log("prog", f"{prog}  total={f.total_reward}", C.DIM)

    log("done", f"{f.ads_done} ads, +{f.total_reward} coins", C.BGRN)


def summarize(state):
    farm = state.get("farm") or {}
    prof = state.get("profile") or {}
    plots = farm.get("plots", [])
    R = sum(1 for p in plots if p.get("state") == "ready")
    G_ = sum(1 for p in plots if p.get("state") == "growing")
    E = sum(1 for p in plots if p.get("state") == "empty" and not p.get("locked"))
    L = sum(1 for p in plots if p.get("state") == "locked")

    log("frm", f"lvl={farm.get('farmLevel')} water={farm.get('water')}/{farm.get('waterMax')} "
        f"{R}R/{G_}G/{E}E/{L}L today={prof.get('todayEarned')} usdt={prof.get('usdt')}",
        C.DIM)


def main_loop(f):
    ads_enabled = True
    ads_rounds_done = 0
    max_ads_rounds = 3

    while not G["STOP"]:
        try:
            state = f.farm()
        except Exception as e:
            log("err", f"Farm fetch: {e}", C.RED)
            time.sleep(30)
            continue

        summarize(state)

        wait_h = 0.0
        for _ in range(6):
            attempted, w = phase_harvest(f, state)
            if w > wait_h:
                wait_h = w
            if attempted:
                try:
                    state = f.farm()
                except Exception:
                    break
            else:
                break

        if phase_plant(f, state):
            try:
                state = f.farm()
            except Exception:
                pass

        if phase_water(f, state):
            try:
                state = f.farm()
            except Exception:
                pass

        if ads_enabled and ads_rounds_done < max_ads_rounds:
            log("ads", f"Ads round #{ads_rounds_done + 1}", C.BMAG)
            run_ads_round(f)
            ads_rounds_done += 1

            try:
                state = f.farm()
            except Exception:
                pass

        now_ms = time.time() * 1000.0
        any_ready_now = False
        earliest_future = None

        for p in (state.get("farm") or {}).get("plots", []):
            st = p.get("state")
            if st == "ready":
                any_ready_now = True
            elif st == "growing":
                ra = p.get("readyAt") or 0
                if ra <= now_ms:
                    any_ready_now = True
                else:
                    gap = (ra - now_ms) / 1000.0
                    if earliest_future is None or gap < earliest_future:
                        earliest_future = gap

        if any_ready_now:
            wait = max(TICK_MIN, wait_h) if wait_h > 0 else TICK_MIN
        elif earliest_future is not None:
            wait = max(TICK_MIN, earliest_future + 1.0)
        else:
            wait = TICK_MAX

        if wait_h > 0:
            wait = max(wait, min(wait_h, TICK_MAX))

        log("frm", f"Next in {human_secs(wait)}", C.DIM)
        time.sleep(wait)


# ============================================================
#   SIGNAL
# ============================================================
def signal_handler(sig, frame):
    print()
    log("stp", "Ctrl+C — stopping...", C.YEL)
    G["STOP"] = True


# ============================================================
#   MAIN
# ============================================================
async def async_main():
    signal.signal(signal.SIGINT, signal_handler)

    print()
    banner()

    # ⬇️ Prompt config manual
    prompt_login_config()

    # Generate FP & DEVICE_ID kalau kosong
    global FP, DEVICE_ID
    if not FP:
        FP = hashlib.md5(os.urandom(16)).hexdigest()[:16]
        log("cfg", f"FP auto-generated: {FP}", C.CYN)
    if not DEVICE_ID:
        DEVICE_ID = f"dev_{hashlib.md5(os.urandom(16)).hexdigest()[:24]}"
        G["DEVICE_ID"] = DEVICE_ID
        log("cfg", f"DEVICE_ID auto-generated: {DEVICE_ID}", C.CYN)

    if not await telethon_login():
        log("err", "Telethon gagal, keluar", C.RED)
        return

    f = Farm()
    if not await f.login_async():
        log("err", "Login gagal, keluar", C.RED)
        return

    log("go", "🚀 Mulai farming + ads...", C.BGRN)
    print()
    main_loop(f)

    log("done", "Selesai", C.BGRN)
    if G["TG_CLIENT"]:
        await G["TG_CLIENT"].disconnect()


def main():
    if not HAS_TELETHON:
        print("❌ Install Telethon dulu: pip install telethon")
        sys.exit(1)

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print()
        print(f"{C.YEL}  Bye!{C.RST}")
    except Exception as e:
        print()
        print(f"{C.RED}  Fatal: {e}{C.RST}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()