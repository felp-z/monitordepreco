import re

def parse_price(text: str) -> float | None:
    if not text:
        return None
    # Remove R$, spaces
    text = re.sub(r'[R$\s]', '', text)
    if not text:
        return None
    
    # Handle formats like 1.299,90 or 1299.90 or 1299,90
    if ',' in text and '.' in text:
        # Check which one is the decimal separator
        if text.rfind(',') > text.rfind('.'):
            # 1.299,90
            text = text.replace('.', '').replace(',', '.')
        else:
            # 1,299.90
            text = text.replace(',', '')
    elif ',' in text:
        text = text.replace(',', '.')
    
    try:
        return float(text)
    except ValueError:
        return None

def format_price(value: float) -> str:
    # Format to BRL format (R$ 1.299,90)
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {formatted}"
