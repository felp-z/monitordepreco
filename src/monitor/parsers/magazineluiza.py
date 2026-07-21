from .base import BaseParser, ParseResult
from ..utils.price import parse_price
from selectolax.parser import HTMLParser

class MagaluParser(BaseParser):
    store_name = 'magazineluiza'
    domains = ['magazineluiza.com.br']

    def extract_price(self, html: str, url: str) -> ParseResult:
        result = ParseResult(price=None, name=None, available=False)
        
        json_ld = self._find_json_ld(html)
        if json_ld and 'offers' in json_ld:
            offers = json_ld['offers']
            if isinstance(offers, dict):
                result.price = float(offers.get('price', 0))
                result.available = offers.get('availability', '').endswith('InStock')
            result.name = json_ld.get('name')
            if result.price:
                return result

        meta_price = self._find_meta_price(html)
        if meta_price:
            result.price = meta_price
            result.available = True
            return result

        parser = HTMLParser(html)
        price_node = parser.css_first('[data-testid="price-value"]')
        if price_node:
            result.price = parse_price(price_node.text())
            result.available = result.price is not None
            
        return result
