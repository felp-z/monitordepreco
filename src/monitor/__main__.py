import asyncio
import logging
import os
import argparse
from pathlib import Path

from .config import load_config
from .scraper import run_all
from .history import load_history, save_history, update_history
from .notifier import CooldownManager, send_alert

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_dotenv():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'\"")

async def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run without sending alerts")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    config = load_config(config_path)
    
    history_path = Path("price_history.json")
    history = load_history(history_path)
    
    cooldown_mgr = CooldownManager()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    logger.info("Starting scrape...")
    results = await run_all(config)
    
    for product in config.products:
        if not product.active:
            continue
            
        product_results = results.get(product.id, {})
        update_history(history, product.id, product.name, product_results)
        
        for link in product.links:
            store = link.store
            res = product_results.get(store)
            if res and res.price and res.available:
                if res.price <= product.target_price:
                    if config.settings.telegram_enabled and not args.dry_run and bot_token and chat_id:
                        if cooldown_mgr.can_notify(product.id, store, config.settings.cooldown_minutes):
                            logger.info(f"Sending alert for {product.name} at {store}!")
                            await send_alert(bot_token, chat_id, product.name, store, res.price, product.target_price, str(link.url))
                            cooldown_mgr.mark_notified(product.id, store)
                        else:
                            logger.info(f"Skipping alert for {product.name} at {store} (cooldown)")
                    else:
                        logger.info(f"Target price reached for {product.name} at {store}: {res.price}")
                        
    save_history(history_path, history)
    logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(main())
