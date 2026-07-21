import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from .utils.price import format_price

logger = logging.getLogger(__name__)

STORE_DISPLAY = {
    "kabum": "Kabum",
    "pichau": "Pichau",
    "terabyte": "Terabyte",
    "amazon": "Amazon",
    "magazineluiza": "Magazine Luiza",
    "americanas": "Americanas",
    "livelo": "Livelo",
    "mercadolivre": "Mercado Livre",
    "shopee": "Shopee",
}


class CooldownManager:
    """Prevents spamming alerts for the same product/store combo."""

    def __init__(self, path: str | Path = ".cooldowns.json") -> None:
        self.path = Path(path)
        self.cooldowns: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(self.cooldowns, indent=2), encoding="utf-8"
        )

    def can_notify(self, product_id: str, store: str, cooldown_minutes: int) -> bool:
        key = f"{product_id}:{store}"
        if key in self.cooldowns:
            last = datetime.fromisoformat(self.cooldowns[key])
            if datetime.now() - last < timedelta(minutes=cooldown_minutes):
                return False
        return True

    def mark_notified(self, product_id: str, store: str) -> None:
        key = f"{product_id}:{store}"
        self.cooldowns[key] = datetime.now().isoformat()
        self._save()


async def send_alert(
    bot_token: str,
    chat_id: str,
    product_name: str,
    store: str,
    current_price: float,
    target_price: float,
    url: str,
) -> None:
    """Send a Telegram alert when price drops below target."""
    bot = Bot(token=bot_token)
    store_display = STORE_DISPLAY.get(store, store.capitalize())

    saving = target_price - current_price
    pct = (saving / target_price) * 100

    text = (
        f"🔥 <b>PREÇO ABAIXO DO ALVO!</b> 🔥\n\n"
        f"📦 <b>{product_name}</b>\n"
        f"🏪 {store_display}\n"
        f"💰 <b>{format_price(current_price)}</b> (alvo: {format_price(target_price)})\n"
        f"📉 Economia: {format_price(saving)} ({pct:.1f}%)\n\n"
        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛒 Comprar Agora", url=url)]]
    )

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info(f"Alert sent for {product_name} at {store_display}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
