from datetime import datetime, date

def format_datetime(value):
    """Formata uma data/hora para o formato DD/MM/AAAA."""
    try:
        if isinstance(value, (datetime, date)):
            return value.strftime("%d/%m/%Y")
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value  # Retorna o valor original se não puder ser formatado
