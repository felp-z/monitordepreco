from .base import BaseParser, ParseResult
from ..utils.price import parse_price
from selectolax.parser import HTMLParser

class LiveloParser(BaseParser):
    store_name = 'livelo'
    domains = ['livelo.com.br']

    def extract_price(self, html: str, url: str) -> ParseResult:
        result = ParseResult(price=None, name=None, available=False)
        
        next_data = self._find_next_data(html)
        if next_data:
            try:
                components = next_data.get('props', {}).get('pageProps', {}).get('page', {}).get('components', [])
                for comp in components:
                    props = comp.get('props', {})
                    if 'product' in props:
                        prod = props['product']
                        skus = prod.get('skus', [])
                        if skus:
                            sku = skus[0]
                            prices = sku.get('prices', {})
                            price = prices.get('cashSalePrice')
                            if price:
                                result.price = float(price)
                                result.available = sku.get('available', True)
                                result.name = prod.get('displayName')
                                return result
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

        meta_price = self._find_meta_price(html)
        if meta_price:
            result.price = meta_price
            result.available = True
            return result

        parser = HTMLParser(html)
        price_node = parser.css_first('[data-testid="product-price"]')
        if price_node:
            result.price = parse_price(price_node.text())
            result.available = result.price is not None
            
        return result
