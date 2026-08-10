import os
import json
import requests
from datetime import datetime
import pytz
import yfinance as yf

# === CONFIG ===
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
PRICE_SOURCE = os.environ.get("PRICE_SOURCE", "GC=F")  # Yahoo Finance ticker
CURRENCY = os.environ.get("CURRENCY", "$")

# === TIMEZONES ===
TZ_TOKYO = pytz.timezone("Asia/Tokyo")
TZ_LONDON = pytz.timezone("Europe/London")
TZ_NY = pytz.timezone("America/New_York")
TZ_UTC = pytz.utc

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

def get_session_status():
    now_utc = now_in_tz(TZ_UTC)
    
    sessions = {
        "Tokyo": {"tz": TZ_TOKYO, "start": 0, "end": 9, "flag": "🇯🇵"},
        "London": {"tz": TZ_LONDON, "start": 8, "end": 17, "flag": "🇬🇧"},
        "New York": {"tz": TZ_NY, "start": 13, "end": 22, "flag": "🇺🇸"},
    }
    
    active = []
    for name, info in sessions.items():
        local_now = now_utc.astimezone(info["tz"])
        hour = local_now.hour
        is_open = info["start"] <= hour < info["end"]
        if is_open:
            active.append(f"{info['flag']} {name}")
    
    return active

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

def session_start_message(session_name):
    price, change, pct = get_price_change()
    current_price = price or get_gold_price()
    
    active_sessions = get_session_status()
    sessions_text = " | ".join(active_sessions) if active_sessions else "No major session active"
    
    # Determine color based on change
    if change is not None:
        color = 65280 if change >= 0 else 16711680  # Green or Red
    else:
        color = 16766720  # Gold
    
    description = f"""**Current Price:** {format_price(current_price)}
**Previous Session Change:** {format_price(change)} ({pct:+.2f}%)
**Active Sessions:** {sessions_text}

Gold is currently trading at {format_price(current_price)}. """
    
    send_discord_embed(
        title=f"🥇 {session_name} Session Start — XAUUSD",
        description=description,
        color=color
    )

def main():
    print(f"DEBUG ENV: webhook_set={bool(DISCORD_WEBHOOK_URL)} price_source={PRICE_SOURCE!r} currency={CURRENCY!r}")
    if not DISCORD_WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL not set")
        return
    
    now_utc = now_in_tz(TZ_UTC)
    hour_utc = now_utc.hour
    
    # Determine which session is starting
    # Tokyo: 00:00 UTC, London: 08:00 UTC, NY: 13:30 UTC approx
    if hour_utc == 0:
        session_start_message("Tokyo")
    elif hour_utc == 8:
        session_start_message("London")
    elif hour_utc == 13:
        session_start_message("New York")
    else:
        # Regular price update
        price = get_gold_price()
        send_discord_embed(
            title="🥇 XAUUSD Price Update",
            description=f"**Gold Spot:** {format_price(price)}",
            color=16766720
        )

if __name__ == "__main__":
    main()
