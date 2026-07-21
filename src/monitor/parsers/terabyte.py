from .base import BaseParser, ParseResult
from ..utils.price import parse_price
from selectolax.parser import HTMLParser

class TerabyteParser(BaseParser):
    store_name = 'terabyte'
    domains = ['terabyteshop.com.br']

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

        parser = HTMLParser(html)
        price_node = parser.css_first('.valor_avista') or parser.css_first('.preco_desconto')
        if price_node:
            result.price = parse_price(price_node.text())
            result.available = result.price is not None
            
        return result
