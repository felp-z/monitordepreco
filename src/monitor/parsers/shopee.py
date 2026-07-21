import json
import re
from .base import BaseParser, ParseResult
from selectolax.parser import HTMLParser

class ShopeeParser(BaseParser):
    store_name = 'shopee'
    domains = ['shopee.com.br']

    def extract_price(self, html: str, url: str) -> ParseResult:
        result = ParseResult(price=None, name=None, available=False)
        
        # Try finding __INITIAL_STATE__
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html)
        if match:
            try:
                state = json.loads(match.group(1))
                # prices in shopee are scaled by 100000
                pass
            except Exception:
                pass
                
        json_ld = self._find_json_ld(html)
        if json_ld and 'offers' in json_ld:
            offers = json_ld['offers']
            if isinstance(offers, dict):
                result.price = float(offers.get('price', 0))
                result.available = offers.get('availability', '').endswith('InStock')
            result.name = json_ld.get('name')
            if result.price:
                return result

        return result
