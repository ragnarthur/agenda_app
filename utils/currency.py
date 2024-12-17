﻿def parse_currency(value):
    """Converte string monetária (R$ 1.234,56) para float."""
    if value:
        return float(value.replace('.', '').replace(',', '.'))
    return 0.0