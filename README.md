# QQQ Gap Analysis

Analýza pravděpodobnosti gap up po extrémních denních propadech na burze (QQQ - Nasdaq 100 ETF).

## Popis

Skript stahuje posledních 5 let denních dat QQQ, identifikuje extrémní denní propady a počítá, jak často následující den otevře gapem nahoru (open > předchozí close).

**Klíčové funkce:**
- Automatické stažení historických dat z Yahoo Finance
- Identifikace extrémních propadů podle procenta nebo percentilu
- Výpočet pravděpodobnosti gap up následujícího dne
- 95% Wilsonovo konfidenční pásmo pro přesnější odhad
- Export výsledků do CSV

## Struktura projektu

```
Finance/
├── .venv/                 # Virtuální prostředí (společné pro všechny skripty)
├── src/                   # Python skripty
│   ├── qqq_gap_analysis.py
│   ├── config.py
│   └── ...další skripty...
├── scripts/               # Setup a aktivační skripty
│   ├── setup.ps1         # Setup na Windows
│   ├── setup.sh          # Setup na macOS/Linux
│   ├── activate.ps1      # Aktivace na Windows
│   └── activate.sh       # Aktivace na macOS/Linux
├── requirements.txt       # Závislosti
└── README.md
```

## Instalace

### Windows

1. Spusťte setup skript:
```powershell
.\scripts\setup.ps1
```

2. Aktivujte prostředí:
```powershell
.\scripts\activate.ps1
```

### macOS / Linux

1. Spusťte setup skript:
```bash
bash scripts/setup.sh
```

2. Aktivujte prostředí:
```bash
source scripts/activate.sh
```

Setup skript automaticky vytvoří virtuální prostředí a nainstaluje všechny závislosti z `requirements.txt`.

### Manuální instalace

```bash
# Vytvoření virtuálního prostředí
python -m venv .venv

# Aktivace prostředí
# Na Windows:
.venv\Scripts\activate
# Na macOS/Linux:
source .venv/bin/activate

# Instalace závislostí
pip install -r requirements.txt
```

## Použití

### Výchozí nastavení (-3% práh, 5 let dat)

```bash
python src/qqq_gap_analysis.py
```

### Vlastní procentuální práh

```bash
python src/qqq_gap_analysis.py --threshold -2.5
python src/qqq_gap_analysis.py --threshold -5.0
```

### Podle percentilu

```bash
python src/qqq_gap_analysis.py --percentile 5
python src/qqq_gap_analysis.py --percentile 10
```

### Jiný počet let

```bash
python src/qqq_gap_analysis.py --years 10
python src/qqq_gap_analysis.py --years 1 --threshold -3.0
```

### Uložení výsledků do CSV

```bash
python src/qqq_gap_analysis.py --threshold -3.0 --save
python src/qqq_gap_analysis.py --percentile 5 --save --years 10
```

## Možnosti

```
--threshold FLOAT      Procentuální práh pro extrémní propady (např. -3.0)
--percentile FLOAT     Percentil nejhorších propadů (např. 5)
--years INT            Počet let pro analýzu (výchozí: 5)
--save                 Uloží výsledky do CSV souboru
--symbol STR           Ticker symbol (výchozí: QQQ)
--no-cache             Ignoruje cache a stáhne data z Yahoo Finance
--cache-info           Zobrazí informace o uložených datech a skončí
--clear-cache          Vymaže cache pro daný symbol
-h, --help            Zobrazí pomoc
```

## Cache systém

Skript automaticky ukládá stažená data do lokální SQLite databáze (`market_data.db`).

### Jak funguje:
1. **Při spuštění**: Skript nejdřív kontroluje, zda jsou data v cache
2. **Pokud ano**: Načte je z cache (mnohem rychlejší)
3. **Pokud ne**: Stáhne je z Yahoo Finance a uloží do cache

### Příkazy pro správu cache:

```bash
# Zobrazí informace o cache pro QQQ
python src/qqq_gap_analysis.py --cache-info

# Vymaže cache pro QQQ
python src/qqq_gap_analysis.py --clear-cache

# Vymaže cache a načte nová data z Yahoo Finance
python src/qqq_gap_analysis.py --clear-cache --no-cache

# Bez použití cache (vždy stahuje z Yahoo Finance)
python src/qqq_gap_analysis.py --no-cache
```

Databáze se vytváří automaticky v aktuálním adresáři a obsahuje tabulky:
- `price_data` - Cenovými údaje (Open, High, Low, Close, Volume)
- `metadata` - Informace o posledné aktualizaci a rozsahu dat

## Výstup

Skript vyprintuje:

1. **Počty**: Celkový počet extrémních propadů a dnů s gapem nahoru
2. **Pravděpodobnost**: Bodový odhad a 95% Wilsonovo konfidenční interval
3. **Statistika gapů**: Průměr, medián, std. dev.
4. **Statistika propadů**: Průměr, minimum, maximum
5. **Tabulka**: Prvních 10 případů s detaily

### Příklad výstupu:

```
Stahování dat QQQ od 2020-12-09 do 2025-12-09...
Staženo 1258 obchodních dnů

Identifikováno 47 dnů s propadem < -3.0%

======================================================================
VÝSLEDKY ANALÝZY
======================================================================

Po extrémních propadech:
  Celkový počet případ: 46
  Dnů s gapem nahoru: 28
  Dnů bez gapu nahoru: 18

Pravděpodobnost gap up:
  Bodový odhad: 60.87%
  95% Wilsonovo CI: [46.36%, 74.08%]

Statistika gapů:
  Průměrný gap: 0.85%
  Medián gapu: 0.42%
  Std. dev gapu: 1.23%

Statistika propadů:
  Průměrný propád: -3.89%
  Nejhorší propád: -12.34%
  Nejlepší propád: -3.01%

======================================================================
Prvních 10 případů:
======================================================================
        Date  Drop_Return  Next_Gap_Percent  Gap_Up
  2020-12-28        -3.50              1.02    True
  2021-01-28        -5.20              0.58    True
  ...
```

## Wilsonovo konfidenční pásmo

Skript používá Wilsonovo konfidenční pásmo místo jednoduchého binomického CI, protože:
- Funguje lépe pro malé vzorky
- Není symetrické kolem bodového odhadu
- Lépe respektuje omezení pravděpodobnosti [0, 1]

## Požadavky

- Python 3.7+
- pandas
- yfinance
- scipy
- numpy

## Licenční podmínky

MIT License

## Autor

Finanční analýza QQQ - 2025
