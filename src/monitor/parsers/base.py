from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import re
from selectolax.parser import HTMLParser

@dataclass
class ParseResult:
    price: float | None
    name: str | None
    available: bool
    currency: str = "BRL"
    original_text: str = ""

class BaseParser(ABC):
    store_name: str
    domains: list[str]
    
    def matches(self, url: str) -> bool:
        return any(d in url for d in self.domains)
    
    @abstractmethod
    def extract_price(self, html: str, url: str) -> ParseResult:
        pass
    
    def _find_json_ld(self, html: str) -> dict | None:
        """Extract Product JSON-LD from HTML."""
        parser = HTMLParser(html)
        for node in parser.css('script[type="application/ld+json"]'):
            try:
                data = json.loads(node.text())
                if isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        return data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            return item
            except Exception:
                continue
        return None
        
    def _find_meta_price(self, html: str) -> float | None:
        """Extract price from og:price:amount or product:price:amount meta tags."""
        parser = HTMLParser(html)
        for prop in ['og:price:amount', 'product:price:amount']:
            node = parser.css_first(f'meta[property="{prop}"]')
            if node and node.attributes.get('content'):
                try:
                    return float(node.attributes.get('content'))
                except ValueError:
                    continue
        return None
        
    def _find_next_data(self, html: str) -> dict | None:
        """Extract __NEXT_DATA__ JSON from script tag."""
        parser = HTMLParser(html)
        node = parser.css_first('script#__NEXT_DATA__')
        if node:
            try:
                return json.loads(node.text())
            except Exception:
                return None
        return None
