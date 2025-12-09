import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print(f"Aktuální čas: {datetime.now()}")

# Stáhneme data pro QQQ (posledních 5 dní)
# yfinance stahuje 'today' pokud je market open
end_date = datetime.now().date() + timedelta(days=1)
start_date = end_date - timedelta(days=5)

print(f"Stahuji data od {start_date} do {end_date}...")
df = yf.download("QQQ", start=start_date, end=end_date, progress=False, auto_adjust=True)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

print("\nPoslední 3 řádky:")
print(df.tail(3))

last_date = df.index[-1].date()
today = datetime.now().date()

print(f"\nPoslední datum v datech: {last_date}")
print(f"Dnešní datum: {today}")

if last_date == today:
    print("✅ Data obsahují dnešní den (Live/Intraday).")
else:
    print("⚠️ Data NEobsahují dnešní den (Market Closed nebo zpoždění).")
