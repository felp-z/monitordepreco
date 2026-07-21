import json
from pathlib import Path
from pydantic import BaseModel, HttpUrl, Field

class StoreLink(BaseModel):
    store: str
    url: HttpUrl

class Product(BaseModel):
    id: str
    name: str
    target_price: float
    active: bool = True
    links: list[StoreLink]

class Settings(BaseModel):
    telegram_enabled: bool = True
    cooldown_minutes: int = 120
    max_concurrent: int = 3
    request_delay: tuple[int, int] = (2, 5)
    firecrawl_enabled: bool = True

class Config(BaseModel):
    products: list[Product]
    settings: Settings

def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Config.model_validate(data)
