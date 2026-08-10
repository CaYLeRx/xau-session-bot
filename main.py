import os
import time
import requests
from datetime import datetime, timedelta
import pytz
import yfinance as yf

# === CONFIG ===
DISCORD_WEBHOOK_URL = (
    os.environ.get("DISCORD_WEBHOOK_URL")
    or os.environ.get("DISCORD_WEBHOOK")
    or os.environ.get("WEBHOOK_URL")
)
if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL is required")
PRICE_SOURCE = os.environ.get("PRICE_SOURCE", "GC=F")
CURRENCY = os.environ.get("CURRENCY", "$")

# === DEBUG ===
print(f"DEBUG ENV candidates: webhook_set={bool(DISCORD_WEBHOOK_URL)} price_source={PRICE_SOURCE!r} currency={CURRENCY!r}")
print(f"DEBUG ENV keys: {sorted(k for k in os.environ if 'WEBHOOK' in k.upper() or 'DISCORD' in k.upper())}")

# === TIMEZONES ===
TZ_TOKYO = pytz.timezone("Asia/Tokyo")
TZ_LONDON = pytz.timezone("Europe/London")
TZ_NY = pytz.timezone("America/New_York")
TZ_UTC = pytz.utc

# === SESSIONS ===
SESSIONS = [
    {"name": "Tokyo", "tz": TZ_TOKYO, "start": 0, "end": 9, "flag": "🇯🇵"},
    {"name": "London", "tz": TZ_LONDON, "start": 8, "end": 17, "flag": "🇬🇧"},
    {"name": "New York", "tz": TZ_NY, "start": 13, "end": 22, "flag": "🇺🇸"},
]

def now_in_tz(tz):
    return datetime.now(tz)

def get_gold_price():
    try:
        ticker = yf.Ticker(PRICE_SOURCE)
        data = ticker.history(period="1d")
        if not data.empty:
            return round(float(data["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"Price fetch error: {e}")
    return None

def get_price_change():
    try:
        ticker = yf.Ticker(PRICE_SOURCE)
        data = ticker.history(period="2d")
        if len(data) >= 2:
            current = float(data["Close"].iloc[-1])
            previous = float(data["Close"].iloc[-2])
            change = current - previous
            pct = (change / previous) * 100
            return current, change, pct
    except Exception as e:
        print(f"Change fetch error: {e}")
    return None, None, None

def format_price(price):
    if price is None:
        return "N/A"
    return f"{CURRENCY}{price:,.2f}"

def send_discord_embed(title, description, color=16766720):
    if not DISCORD_WEBHOOK_URL:
        print("No webhook URL configured")
        return
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "footer": {
            "text": f"XAUUSD Session Bot • {now_in_tz(TZ_UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        }
    }
    payload = {"embeds": [embed]}
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 204:
            print(f"Sent: {title}")
        else:
            print(f"Discord error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Send error: {e}")

def get_active_sessions():
    now_utc = now_in_tz(TZ_UTC)
    active = []
    for info in SESSIONS:
        local_now = now_utc.astimezone(info["tz"])
        hour = local_now.hour
        if info["start"] <= hour < info["end"]:
            active.append(f"{info['flag']} {info['name']}")
    return active

def session_start_message(session_name):
    price, change, pct = get_price_change()
    current_price = price or get_gold_price()
    active_sessions = get_active_sessions()
    sessions_text = " | ".join(active_sessions) if active_sessions else "No major session active"
    
    if change is not None:
        color = 65280 if change >= 0 else 16711680
    else:
        color = 16766720
    
    description = f"""**Current Price:** {format_price(current_price)}
**Previous Session Change:** {format_price(change)} ({pct:+.2f}%)
**Active Sessions:** {sessions_text}

{session_name} is now open. Gold is trading at {format_price(current_price)}. """
    
    send_discord_embed(
        title=f"🥇 {session_name} Session Start — XAUUSD",
        description=description,
        color=color
    )

def session_end_message(session_name):
    price, change, pct = get_price_change()
    current_price = price or get_gold_price()
    
    if change is not None:
        color = 65280 if change >= 0 else 16711680
    else:
        color = 16766720
    
    description = f"""**Session Result:** {format_price(change)} ({pct:+.2f}%)
**Current Price:** {format_price(current_price)}

{session_name} has closed. Gold is now at {format_price(current_price)}. """
    
    send_discord_embed(
        title=f"🔔 {session_name} Session End — XAUUSD",
        description=description,
        color=color
    )

def get_next_session_event():
    """Calculate the next session event (start or end) and seconds until it."""
    now_utc = now_in_tz(TZ_UTC)
    
    events = []
    for session in SESSIONS:
        start_dt = now_utc.replace(hour=session["start"], minute=0, second=0, microsecond=0)
        end_dt = now_utc.replace(hour=session["end"], minute=0, second=0, microsecond=0)
        events.append((start_dt, session["name"], "start"))
        events.append((end_dt, session["name"], "end"))
    
    events.sort(key=lambda x: x[0])
    
    for event_dt, session_name, event_type in events:
        if event_dt > now_utc:
            return session_name, event_type, (event_dt - now_utc).total_seconds()
    
    tomorrow = now_utc + timedelta(days=1)
    tomorrow_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    return "Tokyo", "start", (tomorrow_midnight - now_utc).total_seconds()

def run():
    if os.environ.get("TEST_MODE", "").strip().lower() in ("1", "true", "yes"):
        send_discord_embed(
            title="✅ XAUUSD Session Bot — TEST",
            description="If you can read this, the bot works.\nWebhook delivery: OK",
            color=65280
        )
        return
    
    active_sessions = get_active_sessions()
    if active_sessions:
        sessions_text = " | ".join(active_sessions)
        send_discord_embed(
            title="🤖 XAUUSD Session Bot — Started",
            description=f"Bot is now online.\n\n**Currently Active:** {sessions_text}\n\nNext post will be at the next session event.",
            color=16766720
        )
    
    print("Bot started. Waiting for session events...")
    
    while True:
        try:
            session_name, event_type, sleep_seconds = get_next_session_event()
            
            if sleep_seconds > 86400:
                sleep_seconds = 86400
            
            next_time = now_in_tz(TZ_UTC) + timedelta(seconds=sleep_seconds)
            print(f"Next event: {session_name} {event_type} at {next_time.strftime('%Y-%m-%d %H:%M UTC')} (in {sleep_seconds/3600:.1f}h)")
            
            time.sleep(sleep_seconds)
            
            if event_type == "start":
                session_start_message(session_name)
            else:
                session_end_message(session_name)
            
            time.sleep(5)
            
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run()
