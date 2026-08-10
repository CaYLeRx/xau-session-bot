# 🥇 XAUUSD Session Bot

A Discord bot that sends XAUUSD (Gold) price updates at major trading session starts.

## Features

- 🥇 Live XAUUSD price updates via Yahoo Finance
- 🕐 Automatic session start notifications:
  - Tokyo Session (00:00 UTC)
  - London Session (08:00 UTC)
  - New York Session (13:00 UTC)
- 📊 Shows price change from previous session
- 🎨 Color-coded embeds (green/red based on price movement)
- 💬 Discord webhook integration

## Deployment

This bot is designed to run on [Railway.app](https://railway.app).

### Setup

1. Create a new GitHub repository
2. Push these files to the repository
3. Connect Railway.app to your GitHub repo
4. Add environment variables in Railway:
   - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
   - `PRICE_SOURCE`: Yahoo Finance ticker (default: `GC=F`)
   - `CURRENCY`: Currency symbol (default: `$`)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for sending messages | Required |
| `PRICE_SOURCE` | Yahoo Finance ticker symbol for gold | `GC=F` |
| `CURRENCY` | Currency symbol to display | `$` |

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

## License

MIT
