#!/usr/bin/env python3
"""
ALPHA HUNTER — Real-time smart money signal bot for Solana meme coins.
Combines multiple gmgn.ai data sources to find runners BEFORE retail.

Data sources (ALL free, no auth required):
  1. 1-minute ranking (smart money activity in real-time)
  2. TG channel calls (KOL alpha with win rates)
  3. Smart money signal feed (accumulation alerts)
  4. Wallet config intel (read other traders' strategies)

Run: python3 alpha_hunter.py
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

POLL_INTERVAL_RANKING = 10      # seconds between 1-min ranking polls
POLL_INTERVAL_TG = 20           # seconds between TG message polls
POLL_INTERVAL_SIGNALS = 30      # seconds between signal rank polls

# FILTERS — tune these for your risk tolerance
MIN_SMART_COUNT = 15            # minimum smart money wallets buying
MAX_MCAP = 500_000              # maximum market cap (where 100x is possible)
MIN_MCAP = 10_000               # minimum (below this = likely dead)
MIN_TG_WINRATE = 0.50           # minimum channel win rate to trust
MAX_TOKEN_AGE_MINUTES = 120     # ignore tokens older than this

# ALERTING
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID", "")
ALERT_SOUND = True

# GMGN API (no auth needed for these endpoints)
BASE_URL = "https://gmgn.ai"
QS_PARAMS = {
    "device_id": "alpha_hunter_bot",
    "client_id": "gmgn_web_20260718",
    "from_app": "gmgn",
    "os": "web",
}


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Signal:
    token_address: str
    symbol: str
    name: str
    market_cap: float
    smart_count: int
    source: str              # "ranking", "tg_call", "signal_feed"
    channel_name: str = ""
    channel_winrate: float = 0.0
    volume: float = 0.0
    confidence: int = 1      # 1-3 (higher = more sources confirm)
    timestamp: float = field(default_factory=time.time)
    alerted: bool = False

    @property
    def age_minutes(self):
        return (time.time() - self.timestamp) / 60

    @property
    def potential_x(self):
        if self.market_cap > 0:
            return 5_000_000 / self.market_cap  # potential if it hits $5M
        return 0

    def score(self):
        """Higher score = better signal. Max ~100."""
        s = 0
        # Smart money count (max 30 points)
        s += min(self.smart_count / 10, 30)
        # Low mcap bonus (max 25 points)
        if self.market_cap < 100_000:
            s += 25
        elif self.market_cap < 200_000:
            s += 20
        elif self.market_cap < 500_000:
            s += 10
        # Multi-source confirmation (max 20 points)
        s += self.confidence * 7
        # TG channel win rate (max 15 points)
        if self.channel_winrate > 0.55:
            s += 15
        elif self.channel_winrate > 0.50:
            s += 10
        # Volume (max 10 points — active trading = good)
        if self.volume > 5000:
            s += 10
        elif self.volume > 1000:
            s += 5
        return min(s, 100)


# ═══════════════════════════════════════════════════════════════
# GMGN API CLIENT
# ═══════════════════════════════════════════════════════════════

class GmgnClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://gmgn.ai',
            'Referer': 'https://gmgn.ai/',
        }

    def _build_url(self, path: str, extra_params: dict = None) -> str:
        params = {**QS_PARAMS}
        if extra_params:
            params.update(extra_params)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{BASE_URL}{path}?{qs}"

    async def get(self, path: str, params: dict = None) -> dict:
        url = self._build_url(path, params)
        try:
            async with self.session.get(url, headers=self.headers, timeout=15) as r:
                if r.status == 200:
                    return await r.json()
                return {"code": r.status, "message": f"HTTP {r.status}"}
        except Exception as e:
            return {"code": -1, "message": str(e)}

    async def get_1m_ranking(self, limit: int = 30) -> list:
        """Get tokens with smart money activity in last 60 seconds."""
        d = await self.get("/defi/quotation/v1/rank/sol/swaps/1m", {
            "orderby": "smart_degen_count",
            "direction": "desc",
            "limit": str(limit)
        })
        if d.get("code") == 0:
            return d.get("data", {}).get("rank", [])
        return []

    async def get_tg_messages(self, limit: int = 30) -> list:
        """Get latest TG alpha channel messages."""
        d = await self.get("/vas/api/v1/tg/messages", {"limit": str(limit)})
        if d.get("code") == 0:
            return d.get("data", {}).get("list", [])
        return []

    async def get_smart_signals(self, signal_type: int = 12, limit: int = 20) -> list:
        """Get smart money signal feed. Types: 12=smart, 14=KOL, 16=whale."""
        d = await self.get("/vas/api/v1/token-signal/rank", {
            "chain": "sol",
            "limit": str(limit),
            "signal_type": str(signal_type)
        })
        if d.get("code") == 0:
            return d.get("data", []) if isinstance(d.get("data"), list) else []
        return []

    async def get_wallet_configs(self, address: str) -> dict:
        """Read a wallet's trading configs (IDOR — works on any address)."""
        d = await self.get("/wallet-api/v1/wallet/get_configs", {
            "chain": "sol",
            "address": address
        })
        if d.get("code") == 0:
            return d.get("data", {}).get("items", {})
        return {}

    async def get_token_security(self, address: str) -> dict:
        """Check if token is honeypot/rug."""
        d = await self.get("/defi/quotation/v1/tokens/security", {
            "chain": "sol",
            "address": address
        })
        if d.get("code") == 0:
            return d.get("data", {})
        return {}


# ═══════════════════════════════════════════════════════════════
# SIGNAL ENGINE
# ═══════════════════════════════════════════════════════════════

class SignalEngine:
    def __init__(self, client: GmgnClient):
        self.client = client
        self.seen_tokens: dict[str, Signal] = {}    # address → Signal
        self.previous_ranking: set = set()           # addresses from last poll
        self.alerts_sent: set = set()                # don't double-alert

    def _is_valid_signal(self, mcap: float, smart: int, age_min: float) -> bool:
        """Filter garbage signals."""
        if mcap < MIN_MCAP or mcap > MAX_MCAP:
            return False
        if smart < MIN_SMART_COUNT:
            return False
        if age_min > MAX_TOKEN_AGE_MINUTES:
            return False
        return True

    async def scan_ranking(self) -> list[Signal]:
        """Scan 1-min ranking for NEW tokens appearing."""
        ranking = await self.client.get_1m_ranking()
        current_addresses = set()
        new_signals = []
        now = time.time()

        for token in ranking:
            addr = token.get("address", "")
            if not addr:
                continue
            current_addresses.add(addr)

            symbol = token.get("symbol", "?")
            name = token.get("name", "")
            mcap = float(token.get("market_cap", 0) or 0)
            smart = int(token.get("smart_degen_count", 0) or 0)
            volume = float(token.get("volume", 0) or 0)
            created = int(token.get("created_timestamp", token.get("open_timestamp", 0)) or 0)
            age_min = (now - created) / 60 if created else 9999

            if not self._is_valid_signal(mcap, smart, age_min):
                continue

            # NEW token appearing = strongest signal
            is_new = addr not in self.previous_ranking and addr not in self.seen_tokens

            if is_new:
                signal = Signal(
                    token_address=addr,
                    symbol=symbol,
                    name=name,
                    market_cap=mcap,
                    smart_count=smart,
                    source="ranking_new",
                    volume=volume,
                    confidence=2,  # new appearance = high confidence
                )
                self.seen_tokens[addr] = signal
                new_signals.append(signal)
            elif addr in self.seen_tokens:
                # Update existing signal with fresh data
                existing = self.seen_tokens[addr]
                if smart > existing.smart_count:
                    existing.smart_count = smart
                    existing.market_cap = mcap
                    existing.volume = volume

        self.previous_ranking = current_addresses
        return new_signals

    async def scan_tg_messages(self) -> list[Signal]:
        """Scan TG messages for fresh alpha calls."""
        messages = await self.client.get_tg_messages()
        new_signals = []
        now = time.time()

        import re
        for msg in messages:
            msg_time = msg.get("message_send_at", 0)
            age_sec = now - msg_time if msg_time else 9999

            # Only process messages < 5 minutes old
            if age_sec > 300:
                continue

            channel = msg.get("channel_name", "")
            winrate = float(msg.get("channel_win_rate", 0) or 0)
            content = msg.get("content", "")

            if winrate < MIN_TG_WINRATE:
                continue

            # Extract contract addresses from message
            # Solana addresses: base58, 32-44 chars, often ending in "pump"
            cas = re.findall(r'[A-HJ-NP-Za-km-z1-9]{32,44}pump', content)
            if not cas:
                cas = re.findall(r'CA:\s*([A-HJ-NP-Za-km-z1-9]{32,44})', content)
            if not cas:
                # Generic base58 that looks like a Solana address
                cas = re.findall(r'\b([A-HJ-NP-Za-km-z1-9]{40,44})\b', content)

            for ca in cas[:1]:  # only first CA per message
                if ca in self.seen_tokens:
                    # Already tracked — boost confidence
                    self.seen_tokens[ca].confidence = min(3, self.seen_tokens[ca].confidence + 1)
                    self.seen_tokens[ca].channel_name = channel
                    self.seen_tokens[ca].channel_winrate = winrate
                else:
                    signal = Signal(
                        token_address=ca,
                        symbol="",  # unknown from TG
                        name="",
                        market_cap=0,
                        smart_count=0,
                        source="tg_call",
                        channel_name=channel,
                        channel_winrate=winrate,
                        confidence=1,
                    )
                    self.seen_tokens[ca] = signal
                    new_signals.append(signal)

        return new_signals

    async def scan_smart_signals(self) -> list[Signal]:
        """Scan smart money signal feed."""
        signals = await self.client.get_smart_signals(signal_type=12)
        new_signals = []
        now = int(time.time())

        for s in signals:
            addr = s.get("token_address", "")
            trigger_at = s.get("trigger_at", 0)
            age_min = (now - trigger_at) / 60 if trigger_at else 9999

            # Only fresh signals (< 30 min)
            if age_min > 30:
                continue

            if addr in self.seen_tokens:
                self.seen_tokens[addr].confidence = min(3, self.seen_tokens[addr].confidence + 1)
            else:
                signal = Signal(
                    token_address=addr,
                    symbol=s.get("symbol", ""),
                    name=s.get("name", ""),
                    market_cap=0,
                    smart_count=0,
                    source="signal_feed",
                    confidence=1,
                )
                self.seen_tokens[addr] = signal
                new_signals.append(signal)

        return new_signals

    def get_actionable_signals(self) -> list[Signal]:
        """Get signals worth acting on, sorted by score."""
        actionable = []
        for signal in self.seen_tokens.values():
            if signal.alerted:
                continue
            if signal.score() >= 30:  # minimum score threshold
                actionable.append(signal)
        return sorted(actionable, key=lambda s: s.score(), reverse=True)


# ═══════════════════════════════════════════════════════════════
# ALERTING
# ═══════════════════════════════════════════════════════════════

async def send_telegram_alert(signal: Signal, session: aiohttp.ClientSession):
    """Send alert to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    score = signal.score()
    emoji = "🔥🔥🔥" if score >= 70 else "🔥🔥" if score >= 50 else "🔥"

    text = f"""{emoji} ALPHA SIGNAL — Score: {score}/100

Token: ${signal.symbol} ({signal.name})
CA: `{signal.token_address}`
MCap: ${signal.market_cap:,.0f}
Smart Money: {signal.smart_count} wallets
Potential: {signal.potential_x:.0f}x (to $5M)
Source: {signal.source}"""

    if signal.channel_name:
        text += f"\nChannel: {signal.channel_name} (WR: {signal.channel_winrate*100:.0f}%)"

    if signal.confidence >= 2:
        text += f"\n⚡ MULTI-SOURCE CONFIRMED (confidence: {signal.confidence})"

    text += f"\n\n🔗 https://gmgn.ai/sol/token/{signal.token_address}"
    text += f"\n⏱ {signal.age_minutes:.0f}min ago"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        async with session.post(url, json=payload, timeout=10) as r:
            pass
    except:
        pass


def print_alert(signal: Signal):
    """Print alert to console."""
    score = signal.score()
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")

    if score >= 70:
        prefix = "\033[91m🔥🔥🔥 HIGH CONFIDENCE\033[0m"
    elif score >= 50:
        prefix = "\033[93m🔥🔥 MEDIUM\033[0m"
    else:
        prefix = "\033[92m🔥 LOW\033[0m"

    print(f"\n{'='*60}")
    print(f"[{now}] {prefix} — Score: {score}/100")
    print(f"  Token: ${signal.symbol} ({signal.name})")
    print(f"  CA: {signal.token_address}")
    print(f"  MCap: ${signal.market_cap:,.0f} | Smart: {signal.smart_count}")
    print(f"  Potential: {signal.potential_x:.0f}x | Vol: ${signal.volume:,.0f}")
    print(f"  Source: {signal.source}", end="")
    if signal.channel_name:
        print(f" | Channel: {signal.channel_name} (WR:{signal.channel_winrate*100:.0f}%)", end="")
    if signal.confidence >= 2:
        print(f" | ⚡CONFIRMED x{signal.confidence}", end="")
    print(f"\n  Link: https://gmgn.ai/sol/token/{signal.token_address}")
    print(f"{'='*60}")

    if ALERT_SOUND:
        print("\a", end="")  # terminal bell


# ═══════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════

async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          ALPHA HUNTER — Smart Money Signal Bot              ║
║                                                              ║
║  Sources: 1-min ranking + TG calls + Signal feed            ║
║  Filters: mcap<$500K, smart>15, WR>50%                      ║
║  Speed: 10-second polling cycle                              ║
║                                                              ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
    """)

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        client = GmgnClient(session)
        engine = SignalEngine(client)

        print(f"[*] Starting signal scan...")
        print(f"[*] Filters: mcap ${MIN_MCAP:,}-${MAX_MCAP:,} | smart >= {MIN_SMART_COUNT} | TG WR >= {MIN_TG_WINRATE*100:.0f}%")
        print(f"[*] Poll intervals: ranking={POLL_INTERVAL_RANKING}s, TG={POLL_INTERVAL_TG}s, signals={POLL_INTERVAL_SIGNALS}s")
        if TELEGRAM_BOT_TOKEN:
            print(f"[*] Telegram alerts: ENABLED")
        else:
            print(f"[*] Telegram alerts: DISABLED (set TG_BOT_TOKEN + TG_CHAT_ID)")
        print()

        last_ranking = 0
        last_tg = 0
        last_signals = 0
        cycle = 0

        try:
            while True:
                now = time.time()
                cycle += 1

                # Scan ranking (fastest — every 10s)
                if now - last_ranking >= POLL_INTERVAL_RANKING:
                    new = await engine.scan_ranking()
                    last_ranking = now
                    if new:
                        for s in new:
                            print_alert(s)
                            await send_telegram_alert(s, session)
                            s.alerted = True

                # Scan TG messages (every 20s)
                if now - last_tg >= POLL_INTERVAL_TG:
                    new = await engine.scan_tg_messages()
                    last_tg = now
                    # Check if TG call matches existing ranking signal (BOOST)
                    for s in new:
                        if s.score() >= 30:
                            print_alert(s)
                            await send_telegram_alert(s, session)
                            s.alerted = True

                # Scan smart money signals (every 30s)
                if now - last_signals >= POLL_INTERVAL_SIGNALS:
                    new = await engine.scan_smart_signals()
                    last_signals = now

                # Check for cross-source confirmations
                actionable = engine.get_actionable_signals()
                for s in actionable:
                    if s.confidence >= 2 and not s.alerted:
                        print_alert(s)
                        await send_telegram_alert(s, session)
                        s.alerted = True

                # Status update every 30 cycles
                if cycle % 30 == 0:
                    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
                    tracked = len(engine.seen_tokens)
                    alerted = sum(1 for s in engine.seen_tokens.values() if s.alerted)
                    print(f"  [{ts}] Tracking {tracked} tokens | Alerted {alerted} | Cycle {cycle}")

                await asyncio.sleep(2)  # small sleep between checks

        except KeyboardInterrupt:
            print("\n\n[*] Shutting down...")
            print(f"[*] Total tokens tracked: {len(engine.seen_tokens)}")
            print(f"[*] Alerts sent: {sum(1 for s in engine.seen_tokens.values() if s.alerted)}")

            # Print summary of best signals found
            best = sorted(engine.seen_tokens.values(), key=lambda s: s.score(), reverse=True)[:10]
            if best:
                print(f"\n  Top signals this session:")
                for s in best:
                    print(f"    Score:{s.score():3d} | ${s.symbol:10s} | mcap=${s.market_cap:>10,.0f} | smart={s.smart_count:3d} | {s.source}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
