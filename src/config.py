"""
QQQ Gap Analysis - Konfigurace

Výchozí hodnoty a nastavení pro analýzu
"""

# Výchozí nastavení
DEFAULT_SYMBOL = "QQQ"
DEFAULT_YEARS = 5
DEFAULT_THRESHOLD = -3.0  # -3% propád

# Analýza
CONFIDENCE_LEVEL = 0.95  # 95% interval
MIN_SAMPLE_SIZE = 10  # Minimální počet případů pro statistickou validitu

# Výstup
OUTPUT_COLUMNS = [
    'Date',
    'Drop_Return',
    'Next_Gap_Percent',
    'Gap_Up'
]

# Formátování
DECIMAL_PLACES = 2
PERCENTAGE_DECIMAL_PLACES = 2
