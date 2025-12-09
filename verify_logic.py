import yfinance as yf
import pandas as pd
import numpy as np

# Stáhneme data
print("Stahuji data pro verifikaci...")
df = yf.download("QQQ", start="2022-01-01", end="2022-12-31", progress=False, auto_adjust=True)

# Fix pro yfinance multi-index columns (pokud existuje)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# 1. Logika skriptu (NOVÁ - Daily Drop: Close vs PrevClose)
df['Script_Drop'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100

# 2. Kontrolní výpočet (Manual Check)
# PrevClose je Close posunuté o 1 den
df['Prev_Close'] = df['Close'].shift(1)
df['Manual_Drop'] = ((df['Close'] - df['Prev_Close']) / df['Prev_Close']) * 100

# 3. Gap Logic
df['Next_Open'] = df['Open'].shift(-1)
# Fix pro pandas assignment warning
next_gap_series = ((df['Next_Open'] - df['Close']) / df['Close']) * 100
df['Next_Gap_Pct'] = next_gap_series
df['Gap_Up'] = df['Next_Open'] > df['Close']

print("\n=== VERIFIKACE NOVÉ LOGIKY (Daily Return) ===")
print("Hledám dny s velkým 'Script Drop' (Close < PrevClose o 3%)")

# Filtrujeme podle logiky skriptu
script_drops = df[df['Script_Drop'] < -3.0].copy()

print(f"Nalezeno {len(script_drops)} dnů (rok 2022, Daily Drop < -3%)")
print("\nUkázka 5 případů:")
print(f"{'Datum':<12} | {'PrevClose':<10} | {'Close':<8} | {'Script Drop %':<15} | {'Manual Drop %':<15} | {'Next Open':<10} | {'Gap Up?':<8} | {'Gap %':<8}")
print("-" * 115)

for date, row in script_drops.head(5).iterrows():
    d_str = date.strftime('%Y-%m-%d')
    print(f"{d_str:<12} | {row['Prev_Close']:<10.2f} | {row['Close']:<8.2f} | {row['Script_Drop']:<15.2f} | {row['Manual_Drop']:<15.2f} | {row['Next_Open']:<10.2f} | {str(row['Gap_Up']):<8} | {row['Next_Gap_Pct']:<8.2f}")

print("\n\n=== VYSVĚTLENÍ ===")
print("Script Drop = (Close - PrevClose) / PrevClose --> Nyní měří celkovou denní změnu")
print("Manual Drop = Ruční kontrolní výpočet pro ověření")
