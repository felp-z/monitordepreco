from .base import BaseParser
from .kabum import KabumParser
from .pichau import PichauParser
from .terabyte import TerabyteParser
from .amazon import AmazonParser
from .magazineluiza import MagaluParser
from .americanas import AmericanasParser
from .livelo import LiveloParser
from .mercadolivre import MercadoLivreParser
from .shopee import ShopeeParser

PARSERS: list[BaseParser] = [
    KabumParser(),
    PichauParser(),
    TerabyteParser(),
    AmazonParser(),
    MagaluParser(),
    AmericanasParser(),
    LiveloParser(),
    MercadoLivreParser(),
    ShopeeParser(),
]

def get_parser(url: str) -> BaseParser | None:
    for parser in PARSERS:
        if parser.matches(url):
            return parser
    return None
