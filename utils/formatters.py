from datetime import datetime, date

def format_datetime(value):
    """Formata uma data/hora para o formato DD/MM/AAAA."""
    if value:
        if isinstance(value, (datetime, date)):
            return value.strftime("%d/%m/%Y")
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    return value
