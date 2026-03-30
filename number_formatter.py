"""
Luca muhasebe programı uyumlu sayı formatlama modülü.
Binlik ayırıcı: YOK, Ondalık ayırıcı: virgül (,)
Örnek: 1250,00 veya 5208,33
"""


def format_number(value, decimal_places=2):
    """
    Sayısal değerleri Luca uyumlu formatta düzenler.
    Binlik ayırıcı nokta KULLANILMAZ, sadece ondalık virgül.
    Örnek: 1250,00  /  5208,33  /  75000
    """
    try:
        if not value and value != 0:
            return value

        if isinstance(value, str):
            cleaned = value.strip().replace(',', '.')
            num_value = float(cleaned)
        else:
            num_value = float(value)

        if num_value > 999999999:
            num_value = 999999999

        if decimal_places > 0:
            # Nokta OLMADAN, sadece virgül ile ondalık
            formatted = f"{num_value:.{decimal_places}f}"
            formatted = formatted.replace('.', ',')
        else:
            formatted = str(int(num_value))

        return formatted
    except (ValueError, TypeError):
        return value
