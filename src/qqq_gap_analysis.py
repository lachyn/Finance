import pandas as pd
import numpy as np
import yfinance as yf
from scipy import stats
import argparse
from datetime import datetime, timedelta
import sqlite3
import os
from pathlib import Path
import warnings

# Potlač FutureWarningy
warnings.filterwarnings('ignore', category=FutureWarning)


class DataCache:
    """Správa SQLite cache pro historická data."""
    
    DB_NAME = "market_data.db"
    
    def __init__(self, db_path=None):
        """Inicializace cache.
        
        Args:
            db_path: Cesta k databázi (výchozí: market_data.db v aktuálním adresáři)
        """
        if db_path is None:
            db_path = self.DB_NAME
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Vytvoří tabulky v databázi, pokud neexistují."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                PRIMARY KEY (symbol, date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                symbol TEXT PRIMARY KEY,
                last_updated TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_cached_data(self, symbol, start_date=None, end_date=None):
        """Získá data z cache, pokud jsou dostupná.
        
        Args:
            symbol: Ticker symbol
            start_date: Počáteční datum (datetime.date)
            end_date: Koncové datum (datetime.date)
        
        Returns:
            DataFrame s daty nebo None, pokud data nejsou v cache
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = f"SELECT * FROM price_data WHERE symbol = '{symbol}'"
            
            if start_date:
                start_str = start_date.strftime('%Y-%m-%d')
                query += f" AND date >= '{start_str}'"
            
            if end_date:
                end_str = end_date.strftime('%Y-%m-%d')
                query += f" AND date <= '{end_str}'"
            
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                return None
            
            # Převeď řetězce na datetime index
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            return df
        
        finally:
            conn.close()
    
    def save_data(self, symbol, df):
        """Uloží data do cache.
        
        Args:
            symbol: Ticker symbol
            df: DataFrame s OHLCV daty
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Připrav data pro vložení - konvertuj na python scalary
        data_to_insert = []
        
        for i in range(len(df)):
            date_val = df.index[i]
            date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)[:10]
            row = df.iloc[i]
            # Převeď na python scalary pomocí astype nebo item()
            data_to_insert.append((
                symbol,
                date_str,
                float(row['Open']),
                float(row['High']),
                float(row['Low']),
                float(row['Close']),
                int(row['Volume'])
            ))
        
        # INSERT OR REPLACE (aktualizuj, pokud existuje)
        cursor.executemany('''
            INSERT OR REPLACE INTO price_data 
            (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data_to_insert)
        
        # Aktualizuj metadata
        if len(df) > 0:
            dates = pd.to_datetime(df.index)
            cursor.execute('''
                INSERT OR REPLACE INTO metadata 
                (symbol, last_updated, start_date, end_date)
                VALUES (?, ?, ?, ?)
            ''', (
                symbol,
                datetime.now().isoformat(),
                dates.min().strftime('%Y-%m-%d'),
                dates.max().strftime('%Y-%m-%d')
            ))
        
        conn.commit()
        conn.close()
    
    def get_metadata(self, symbol):
        """Získá metadata o symbolu.
        
        Returns:
            Dict s informacemi nebo None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT last_updated, start_date, end_date FROM metadata WHERE symbol = ?',
            (symbol,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'last_updated': result[0],
                'start_date': result[1],
                'end_date': result[2]
            }
        return None
    
    def clear_cache(self, symbol=None):
        """Vymaže cache.
        
        Args:
            symbol: Konkrétní symbol (vymaže jen jeho data), nebo None (vymaže vše)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('DELETE FROM price_data WHERE symbol = ?', (symbol,))
            cursor.execute('DELETE FROM metadata WHERE symbol = ?', (symbol,))
            print(f"Cache pro {symbol} vymazána")
        else:
            cursor.execute('DELETE FROM price_data')
            cursor.execute('DELETE FROM metadata')
            print("Veškerá cache vymazána")
        
        conn.commit()
        conn.close()


def download_qqq_data(symbol='QQQ', years=5, use_cache=True, cache=None):
    """Stáhne historická data QQQ, primárně z cache.
    
    Args:
        symbol: Ticker symbol
        years: Počet let pro stažení
        use_cache: Používat cache
        cache: DataCache instance
    
    Returns:
        DataFrame s daty
    """
    if cache is None:
        cache = DataCache()
    
    # Zahrneme i dnešek (yfinance end je exkluzivní, takže +1 den)
    end_date = datetime.now().date() + timedelta(days=1)
    start_date = end_date - timedelta(days=365 * years)
    
    # Pokus se získat z cache
    if use_cache:
        print(f"Kontrola cache pro {symbol}...")
        cached_data = cache.get_cached_data(symbol, start_date, end_date)
        
        if cached_data is not None and len(cached_data) > 0:
            metadata = cache.get_metadata(symbol)
            print(f"Data nalezena v cache (aktualizováno: {metadata['last_updated'][:10]})")
            print(f"Načteno {len(cached_data)} obchodních dnů z cache")
            return cached_data
    
    # Stáhni z Yahoo Finance
    print(f"\nStahování dat {symbol} z Yahoo Finance od {start_date} do {end_date}...")
    qqq = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
    
    if qqq.empty:
        raise ValueError("Nepodařilo se stáhnout data z Yahoo Finance")
    
    print(f"Staženo {len(qqq)} obchodních dnů z Yahoo Finance")
    
    # Ulož do cache
    if use_cache:
        print("Ukládání do cache...")
        cache.save_data(symbol, qqq)
        print("Data uložena do cache")
    
    return qqq


def calculate_daily_return(df):
    """Vypočítá denní procentuální změnu a další technické indikátory."""
    # Standardní denní změna (Close / PrevClose - 1)
    df['Daily_Return'] = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
    df['Gap'] = ((df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
    
    # 1. Relative Volume (RVOL) - poměr aktuálního objemu k 20dennímu průměru
    df['Vol_Avg_20'] = df['Volume'].rolling(window=20).mean()
    df['RVOL'] = df['Volume'] / df['Vol_Avg_20']
    
    # 2. Close Location Value (CLV) - kde v rámci dne jsme zavřeli (0=Low, 1=High)
    # (Close - Low) / (High - Low)
    # Nízká hodnota (< 0.2) znamená, že prodejci tlačili až do konce -> Bearish
    range_len = df['High'] - df['Low']
    # Ošetření dělení nulou
    df['Close_Loc'] = np.where(range_len == 0, 0.5, (df['Close'] - df['Low']) / range_len)
    
    return df


def identify_extreme_drops(df, threshold=None, percentile=None):
    """
    Identifikuje extrémní denní propady.
    
    Args:
        df: DataFrame s cenovými daty
        threshold: Procentuální práh (např. -3.0 pro -3%)
        percentile: Percentil (např. 5 pro 5. percentil nejhorších poklesů)
    
    Returns:
        (DataFrame, float) - Filtrovaná data a použitý práh
    """
    if threshold is None and percentile is None:
        threshold = -3.0  # výchozí práh
    
    cutoff = 0.0
    
    if threshold is not None:
        cutoff = threshold
        extreme_drops = df[df['Daily_Return'] < threshold].copy()
        print(f"\nIdentifikováno {len(extreme_drops)} dnů s propadem < {threshold}%")
    else:
        # Používáme percentil nejhorších propadů
        cutoff = np.percentile(df['Daily_Return'].dropna(), percentile)
        extreme_drops = df[df['Daily_Return'] <= cutoff].copy()
        print(f"\nIdentifikováno {len(extreme_drops)} dnů ({percentile}. percentil, práh {cutoff:.2f}%)")
    
    return extreme_drops, cutoff


def calculate_next_day_gap_up(df, extreme_drops):
    """
    Zjistí, kolik následujících dnů otevřelo gapem nahoru (Open > předchozí Close).
    """
    results = []
    
    for idx in extreme_drops.index:
        if idx == df.index[-1]:  # Poslední den nemá následující den
            continue
        
        current_loc = df.index.get_loc(idx)
        next_loc = current_loc + 1
        
        if next_loc < len(df):
            # Použij .iloc pro řádek - automaticky vrací scalar nebo Series
            current_row = df.iloc[current_loc]
            next_row = df.iloc[next_loc]
            
            # .item() vynucuje konverzi na python scalar bez warningů
            current_close = current_row['Close'].item() if hasattr(current_row['Close'], 'item') else float(current_row['Close'])
            next_open = next_row['Open'].item() if hasattr(next_row['Open'], 'item') else float(next_row['Open'])
            drop_return = current_row['Daily_Return'].item() if hasattr(current_row['Daily_Return'], 'item') else float(current_row['Daily_Return'])
            
            # Nové metriky
            rvol = current_row['RVOL'].item() if hasattr(current_row['RVOL'], 'item') else float(current_row['RVOL'])
            close_loc = current_row['Close_Loc'].item() if hasattr(current_row['Close_Loc'], 'item') else float(current_row['Close_Loc'])
            
            gap_up = next_open > current_close
            gap_percent = ((next_open - current_close) / current_close) * 100
            
            results.append({
                'Date': idx.date() if hasattr(idx, 'date') else str(idx)[:10],
                'Drop_Return': drop_return,
                'RVOL': rvol,
                'Close_Loc': close_loc,
                'Next_Gap_Percent': gap_percent,
                'Gap_Up': gap_up
            })
    
    return pd.DataFrame(results)


def wilson_confidence_interval(successes, n, confidence=0.95):
    """
    Vypočítá Wilsonovo konfidenční pásmo pro binomickou pravděpodobnost.
    
    Args:
        successes: Počet úspěchů
        n: Celkový počet pokusů
        confidence: Úroveň důvěry (výchozí 0.95 = 95%)
    
    Returns:
        (point_estimate, lower_bound, upper_bound)
    """
    if n == 0:
        return 0, 0, 0
    
    p_hat = successes / n
    z = stats.norm.ppf((1 + confidence) / 2)  # 1.96 pro 95%
    
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denominator
    
    lower = max(0, center - margin)
    upper = min(1, center + margin)
    
    return p_hat, lower, upper


def export_results_to_csv(gap_results, threshold=None, percentile=None, years=None, symbol='QQQ'):
    """Exportuje kompletní výsledky analýzy do CSV včetně statistiky."""
    if gap_results is None or len(gap_results) == 0:
        print("Žádné výsledky k exportu.")
        return None
    
    # Připrav statistiku z atributů
    stats = gap_results.attrs.get('stats', {})
    
    # Vytvoř CSV s dvěma částmi: statistika + data
    filename = f"qqq_gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Hlavička se metadata
        f.write("# QQQ GAP-UP ANALÝZA\n")
        f.write(f"# Symbol: {symbol}\n")
        f.write(f"# Období: posledních {years} let\n")
        if threshold:
            f.write(f"# Práh: {threshold}%\n")
        if percentile:
            f.write(f"# Percentil: {percentile}\n")
        f.write(f"# Datum exportu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("#\n")
        
        # Statistika
        f.write("# STATISTIKA\n")
        f.write(f"Celkový počet případů,{stats.get('total_days', 0)}\n")
        f.write(f"Dnů s gapem nahoru,{stats.get('gap_up_days', 0)}\n")
        f.write(f"Dnů bez gapu nahoru,{stats.get('gap_down_days', 0)}\n")
        f.write(f"Pravděpodobnost gap up (%),{stats.get('probability', 0):.2f}%\n")
        f.write(f"95% CI dolní mez (%),{stats.get('ci_lower', 0):.2f}%\n")
        f.write(f"95% CI horní mez (%),{stats.get('ci_upper', 0):.2f}%\n")
        f.write(f"Průměrný gap (%),{stats.get('avg_gap', 0):.2f}%\n")
        f.write(f"Medián gapu (%),{stats.get('median_gap', 0):.2f}%\n")
        f.write(f"Std. dev gapu (%),{stats.get('std_gap', 0):.2f}%\n")
        f.write(f"Průměrný propád (%),{stats.get('avg_drop', 0):.2f}%\n")
        f.write(f"Nejhorší propád (%),{stats.get('min_drop', 0):.2f}%\n")
        f.write(f"Nejlepší propád (%),{stats.get('max_drop', 0):.2f}%\n")
        f.write("#\n")
        f.write("# DETAIL JEDNOTLIVÝCH PŘÍPADŮ\n")
        
        # Detail data - zapiš jako CSV
        gap_results.to_csv(f, index=False, mode='a', header=True)
    
    return filename


def analyze_results(gap_results):
    """Analyzuje výsledky a vypočítá statistiku."""
    if len(gap_results) == 0:
        print("Žádné relevantní následující dny pro analýzu.")
        return
    
    total_days = len(gap_results)
    gap_up_days = gap_results['Gap_Up'].sum()
    
    point_est, lower, upper = wilson_confidence_interval(gap_up_days, total_days)
    
    print("\n" + "="*70)
    print("VÝSLEDKY ANALÝZY")
    print("="*70)
    print(f"\nPo extrémních propadech:")
    print(f"  Celkový počet případ: {total_days}")
    print(f"  Dnů s gapem nahoru: {gap_up_days}")
    print(f"  Dnů bez gapu nahoru: {total_days - gap_up_days}")
    
    print(f"\nPravděpodobnost gap up:")
    print(f"  Bodový odhad: {point_est*100:.2f}%")
    print(f"  95% Wilsonovo CI: [{lower*100:.2f}%, {upper*100:.2f}%]")
    
    print(f"\nStatistika gapů:")
    print(f"  Průměrný gap: {gap_results['Next_Gap_Percent'].mean():.2f}%")
    print(f"  Medián gapu: {gap_results['Next_Gap_Percent'].median():.2f}%")
    print(f"  Std. dev gapu: {gap_results['Next_Gap_Percent'].std():.2f}%")
    
    print(f"\nStatistika propadů:")
    print(f"  Průměrný propád: {gap_results['Drop_Return'].mean():.2f}%")
    print(f"  Nejhorší propád: {gap_results['Drop_Return'].min():.2f}%")
    print(f"  Nejlepší propád: {gap_results['Drop_Return'].max():.2f}%")
    
    print(f"\nAnalýza faktorů (Průměrné hodnoty):")
    print(f"{'Metrika':<15} | {'Gap UP Dny':<12} | {'Gap DOWN Dny':<12} | {'Rozdíl':<10}")
    print("-" * 55)
    
    # Rozděl data
    up_days = gap_results[gap_results['Gap_Up'] == True]
    down_days = gap_results[gap_results['Gap_Up'] == False]
    
    # RVOL
    rvol_up = up_days['RVOL'].mean() if not up_days.empty else 0
    rvol_down = down_days['RVOL'].mean() if not down_days.empty else 0
    print(f"{'RVOL':<15} | {rvol_up:<12.2f} | {rvol_down:<12.2f} | {rvol_up-rvol_down:+.2f}")
    
    # Close Location
    loc_up = up_days['Close_Loc'].mean() if not up_days.empty else 0
    loc_down = down_days['Close_Loc'].mean() if not down_days.empty else 0
    print(f"{'Close Loc (0-1)':<15} | {loc_up:<12.2f} | {loc_down:<12.2f} | {loc_up-loc_down:+.2f}")
    
    print("\n" + "="*70)
    print("Prvních 10 případů:")
    print("="*70)
    print(gap_results.head(10).to_string(index=False))
    
    # Přidej statistiku do dataframe pro CSV export
    gap_results.attrs['stats'] = {
        'total_days': total_days,
        'gap_up_days': gap_up_days,
        'gap_down_days': total_days - gap_up_days,
        'probability': point_est * 100,
        'ci_lower': lower * 100,
        'ci_upper': upper * 100,
        'avg_gap': gap_results['Next_Gap_Percent'].mean(),
        'median_gap': gap_results['Next_Gap_Percent'].median(),
        'std_gap': gap_results['Next_Gap_Percent'].std(),
        'avg_drop': gap_results['Drop_Return'].mean(),
        'min_drop': gap_results['Drop_Return'].min(),
        'max_drop': gap_results['Drop_Return'].max()
    }
    
    return gap_results


def print_current_status(df, cutoff, stats):
    """Vytiskne informaci o aktuálním stavu trhu."""
    if df is None or df.empty:
        return

    last_date = df.index[-1]
    last_row = df.iloc[-1]
    
    # Získej hodnoty bezpečně (scalar)
    last_close = last_row['Close']
    last_drop = last_row['Daily_Return']
    last_rvol = last_row['RVOL'] if 'RVOL' in last_row else 0
    last_loc = last_row['Close_Loc'] if 'Close_Loc' in last_row else 0.5
    
    print("\n" + "="*70)
    print(f"AKTUÁLNÍ STAV TRHU ({last_date.strftime('%Y-%m-%d')})")
    print("="*70)
    
    print(f"  Cena Close:      {last_close:.2f}")
    print(f"  Dnešní změna:    {last_drop:.2f}%")
    print(f"  Signální práh:   {cutoff:.2f}%")
    print(f"  RVOL (Objem):    {last_rvol:.2f}x")
    print(f"  Close Loc:       {last_loc:.2f} (0=Low, 1=High)")
    
    is_signal = last_drop < cutoff
    
    if is_signal:
        print("\n  ⚠️  SIGNÁL AKTIVNÍ! TRH JE V EXTRÉMNÍM PROPADU ⚠️")
        print(f"  --------------------------------------------------")
        print(f"  Historická pravděpodobnost Gap Up zítra: {stats['probability']:.2f}%")
        print(f"  95% Interval spolehlivosti: [{stats['ci_lower']:.2f}% - {stats['ci_upper']:.2f}%]")
        
        print(f"\n  STRATEGICKÉ VYHODNOCENÍ (SHORT vs BOUNCE):")
        print(f"  ------------------------------------------")
        
        # Logika pro vyhodnocení situace
        # Short setup: Zavíráme na dně a není to extrémní kapitulace
        short_cond = last_loc < 0.15 and last_rvol < 2.0
        # Bounce setup: Už se to zvedá ode dna nebo je to masivní kapitulace
        bounce_cond = last_loc > 0.25 or last_rvol > 2.5
        
        if short_cond:
            print("  🔴 SHORT SETUP (Pravděpodobné pokračování poklesu)")
            print("     Důvody:")
            print(f"     1. Close Location {last_loc:.2f} < 0.15 (Prodejci tlačí do konce)")
            print(f"     2. RVOL {last_rvol:.2f} není extrémní (Není to kapitulace)")
        elif bounce_cond:
            print("  🟢 BOUNCE SETUP (Možný odraz / Gap Up)")
            print("     Důvody:")
            if last_loc > 0.25:
                print(f"     1. Close Location {last_loc:.2f} > 0.25 (Někdo už nakupuje)")
            if last_rvol > 2.5:
                print(f"     2. RVOL {last_rvol:.2f} je extrémní (Kapitulace)")
        else:
            print("  ⚪ NEUTRÁLNÍ / NEJASNÝ SIGNÁL")
            print("     - Metriky jsou smíšené, čekej na jasnější potvrzení.")
            
    else:
        diff = last_drop - cutoff
        print(f"\n  Signál není aktivní. (Chybí {diff:.2f}% k dosažení prahu)")


def main():
    parser = argparse.ArgumentParser(
        description='Analýza pravděpodobnosti gap up po extrémních propadech QQQ'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        help='Procentuální práh pro extrémní propady (např. -3.0 pro -3%%)'
    )
    parser.add_argument(
        '--percentile',
        type=float,
        help='Percentil nejhorších propadů (např. 5 pro 5. percentil)'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=5,
        help='Počet let pro analýzu (výchozí: 5)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Uloží výsledky do CSV souboru'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Stáhne data z Yahoo Finance bez kontroly cache'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Vymaže cache a skončí'
    )
    parser.add_argument(
        '--cache-info',
        action='store_true',
        help='Zobrazí informace o cache a skončí'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='QQQ',
        help='Ticker symbol (výchozí: QQQ)'
    )
    
    args = parser.parse_args()
    
    # Inicializuj cache
    cache = DataCache()
    
    # Cache info
    if args.cache_info:
        metadata = cache.get_metadata(args.symbol)
        if metadata:
            print(f"Cache pro {args.symbol}:")
            print(f"  Poslední aktualizace: {metadata['last_updated']}")
            print(f"  Rozsah dat: {metadata['start_date']} až {metadata['end_date']}")
        else:
            print(f"Žádná cache pro {args.symbol}")
        return
    
    # Clear cache
    if args.clear_cache:
        cache.clear_cache(args.symbol)
        return
    
    # Stažení dat
    qqq = download_qqq_data(
        symbol=args.symbol,
        years=args.years,
        use_cache=not args.no_cache,
        cache=cache
    )
    
    # Výpočet denních propadů a gapů
    qqq = calculate_daily_return(qqq)
    
    # Identifikace extrémních propadů
    extreme_drops, cutoff = identify_extreme_drops(
        qqq,
        threshold=args.threshold,
        percentile=args.percentile
    )
    
    # Analýza následujících dnů
    gap_results = calculate_next_day_gap_up(qqq, extreme_drops)
    
    # Výpočet a zobrazení výsledků
    results_df = analyze_results(gap_results)
    
    # Zobrazení aktuálního stavu
    if results_df is not None and hasattr(results_df, 'attrs') and 'stats' in results_df.attrs:
        print_current_status(qqq, cutoff, results_df.attrs['stats'])
    
    # Uložení výsledků
    if args.save and results_df is not None:
        filename = export_results_to_csv(
            results_df, 
            threshold=args.threshold,
            percentile=args.percentile,
            years=args.years,
            symbol=args.symbol
        )
        if filename:
            print(f"\nVýsledky uloženy do: {filename}")


if __name__ == '__main__':
    main()
