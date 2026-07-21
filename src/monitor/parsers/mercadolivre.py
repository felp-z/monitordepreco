from .base import BaseParser, ParseResult
from ..utils.price import parse_price
from selectolax.parser import HTMLParser

class MercadoLivreParser(BaseParser):
    store_name = 'mercadolivre'
    domains = ['mercadolivre.com.br', 'produto.mercadolivre.com.br']

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
        fraction_node = parser.css_first('.andes-money-amount__fraction')
        cents_node = parser.css_first('.andes-money-amount__cents')
        if fraction_node:
            price_text = fraction_node.text()
            if cents_node:
                price_text += ',' + cents_node.text()
            result.price = parse_price(price_text)
            result.available = result.price is not None
            
        return result
