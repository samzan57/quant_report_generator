# quant_calculator.py
import pandas as pd
import numpy as np
from scipy import stats
# Ajoute ces imports en haut du fichier quant_calculator.py
from modules.rolling_metrics import compute_all_rolling
from modules.monte_carlo import monte_carlo_simulation, monte_carlo_var
from modules.backtesting import run_all_strategies
from modules.stress_testing import run_all_stress_tests
from modules.factor_model import run_all_factor_models
from modules.portfolio import run_portfolio_optimization
from modules.signals import run_all_signals
from modules.black_scholes import run_bs_analysis
from modules.monte_carlo_options import run_mc_options_analysis
from modules.heston import run_heston_analysis

def calculate_returns(prices):
    """Calcule les rendements journaliers"""
    return prices.pct_change().dropna()

def calculate_metrics(prices, risk_free_rate=0.02):
    """Calcule tous les métriques quantitatifs"""
    returns = calculate_returns(prices)
    
    metrics = {}

    # Rendements
    metrics['rendement_total'] = float((prices.iloc[-1] / prices.iloc[0] - 1) * 100)
    metrics['rendement_annualise'] = float(returns.mean() * 252 * 100)
    
    # Risque
    metrics['volatilite_quotidienne'] = float(returns.std() * 100)
    metrics['volatilite_annualisee'] = float(returns.std() * np.sqrt(252) * 100)
    
    # Sharpe Ratio
    excess_returns = returns.mean() - risk_free_rate / 252
    metrics['sharpe_ratio'] = float(excess_returns / returns.std() * np.sqrt(252))
    
    # Sortino Ratio
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    metrics['sortino_ratio'] = float((returns.mean() * 252 - risk_free_rate) / downside_std) if downside_std != 0 else 0
    
    # Maximum Drawdown
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    metrics['max_drawdown'] = float(drawdown.min() * 100)
    
    # VaR 95% et 99%
    metrics['var_95'] = float(np.percentile(returns, 5) * 100)
    metrics['var_99'] = float(np.percentile(returns, 1) * 100)
    
    # CVaR (Expected Shortfall)
    metrics['cvar_95'] = float(returns[returns <= np.percentile(returns, 5)].mean() * 100)
    
    # Skewness & Kurtosis
    metrics['skewness'] = float(returns.skew())
    metrics['kurtosis'] = float(returns.kurtosis())
    
    # Beta & Alpha (par rapport au marché simulé)
    market_returns = returns.sample(frac=1).values  # Simulation si pas de benchmark
    slope, intercept, r_value, p_value, std_err = stats.linregress(market_returns, returns.values)
    metrics['beta'] = float(slope)
    metrics['alpha'] = float(intercept * 252 * 100)
    metrics['r_squared'] = float(r_value**2)
    
    # Statistiques de base
    metrics['nb_jours'] = len(prices)
    metrics['prix_debut'] = float(prices.iloc[0])
    metrics['prix_fin'] = float(prices.iloc[-1])
    metrics['prix_max'] = float(prices.max())
    metrics['prix_min'] = float(prices.min())
    metrics['jours_positifs'] = int((returns > 0).sum())
    metrics['jours_negatifs'] = int((returns < 0).sum())
    metrics['win_rate'] = float((returns > 0).mean() * 100)
    
    return metrics, returns

def calculate_moving_averages(prices):
    """Calcule les moyennes mobiles"""
    ma = pd.DataFrame(index=prices.index)
    ma['prix'] = prices
    ma['SMA_20'] = prices.rolling(window=20).mean()
    ma['SMA_50'] = prices.rolling(window=50).mean()
    ma['SMA_200'] = prices.rolling(window=200).mean()
    ma['EMA_20'] = prices.ewm(span=20).mean()
    ma['EMA_50'] = prices.ewm(span=50).mean()
    return ma

def calculate_rsi(prices, period=14):
    """Calcule le RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calcule les Bandes de Bollinger"""
    bb = pd.DataFrame(index=prices.index)
    bb['prix'] = prices
    bb['moyenne'] = prices.rolling(window=period).mean()
    bb['std'] = prices.rolling(window=period).std()
    bb['bande_haute'] = bb['moyenne'] + (std_dev * bb['std'])
    bb['bande_basse'] = bb['moyenne'] - (std_dev * bb['std'])
    return bb

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calcule le MACD"""
    macd = pd.DataFrame(index=prices.index)
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd['macd'] = ema_fast - ema_slow
    macd['signal'] = macd['macd'].ewm(span=signal).mean()
    macd['histogramme'] = macd['macd'] - macd['signal']
    return macd

def calculate_correlation_matrix(dfs):
    """Calcule la matrice de corrélation entre plusieurs actifs"""
    returns_dict = {}
    for name, df in dfs.items():
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            prices = df[numeric_cols[0]].dropna()
            if len(prices) > 1:
                returns_dict[name] = prices.pct_change().dropna()
    
    if len(returns_dict) > 1:
        returns_df = pd.DataFrame(returns_dict).dropna()
        return returns_df.corr()
    return None

def run_full_analysis(dfs, analysis):
    """Lance l'analyse complète sur les données nettoyées"""
    results = {}

    for sheet_name, df in dfs.items():
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        print(f"  Colonnes numériques dans '{sheet_name}': {numeric_cols}")

        if len(numeric_cols) == 0:
            print(f"  ⚠ Aucune colonne numérique dans '{sheet_name}', ignorée")
            continue

        sheet_results = {}

        # Détecter la colonne de prix principale
        close_col = None
        for candidate in ['Close', 'close', 'Adj Close', 'Prix', 'Price']:
            if candidate in df.columns:
                close_col = candidate
                break

        price_col = close_col if close_col else numeric_cols[0]
        print(f"  Colonne de prix utilisée : {price_col}")

        prices = df[price_col].dropna()
        prices = prices[prices > 0]

        # Définir l'index comme date si disponible
        for col in df.columns:
            if any(k in str(col).lower() for k in ['date', 'time']):
                try:
                    prices.index = pd.to_datetime(
                        df.loc[prices.index, col]
                    )
                except:
                    pass
                break

        if len(prices) < 10:
            print(f"  ⚠ Pas assez de données ({len(prices)} lignes), ignorée")
            continue

        print(f"  ✓ {len(prices)} prix valides trouvés")

        # ── Calculs de base ──────────────────────────────────
        metrics, returns = calculate_metrics(prices)
        sheet_results['metrics'] = metrics
        sheet_results['returns'] = returns
        sheet_results['prices'] = prices

        # Indicateurs techniques
        if len(prices) >= 20:
            sheet_results['moving_averages'] = calculate_moving_averages(prices)
            sheet_results['bollinger'] = calculate_bollinger_bands(prices)
        if len(prices) >= 14:
            sheet_results['rsi'] = calculate_rsi(prices)
        if len(prices) >= 26:
            sheet_results['macd'] = calculate_macd(prices)

        # ── Rolling Metrics ──────────────────────────────────
        print(f"  Rolling metrics — {sheet_name}...")
        sheet_results['rolling'] = compute_all_rolling(
            returns, windows=[30, 60, 90]
        )

        # ── Monte Carlo ──────────────────────────────────────
        print(f"  Monte Carlo — {sheet_name}...")
        try:
            simulations, mc_stats = monte_carlo_simulation(
                prices, n_simulations=500, n_days=252
            )
            mc_var, _ = monte_carlo_var(returns)
            sheet_results['monte_carlo'] = {
                'simulations': simulations,
                'stats': mc_stats,
                'var': mc_var,
            }
        except Exception as e:
            print(f"  ⚠ Monte Carlo échoué : {e}")

        # ── Backtesting ──────────────────────────────────────
        print(f"  Backtesting — {sheet_name}...")
        try:
            sheet_results['backtest'] = run_all_strategies(prices)
        except Exception as e:
            print(f"  ⚠ Backtesting échoué : {e}")

        # ── Stress Testing ───────────────────────────────────
        print(f"  Stress testing — {sheet_name}...")
        try:
            sheet_results['stress'] = run_all_stress_tests(returns)
        except Exception as e:
            print(f"  ⚠ Stress testing échoué : {e}")

        # ── Factor Model ─────────────────────────────────────
        print(f"  Factor model — {sheet_name}...")
        try:
            sheet_results['factors'] = run_all_factor_models(returns)
        except Exception as e:
            print(f"  ⚠ Factor model échoué : {e}")

        # ── Signaux de Trading ───────────────────────────────
        print(f"  Signaux de trading — {sheet_name}...")
        try:
            sheet_results['signals'] = run_all_signals(prices)
            if sheet_results['signals']:
                final = sheet_results['signals']['signal_final']
                print(f"    ✓ Signal : {final['signal_final']} "
                      f"(conviction {final['conviction_finale']:.0f}%)")
        except Exception as e:
            print(f"  ⚠ Signaux échoués : {e}")

        # ── Black-Scholes ────────────────────────────────────
        print(f"  Black-Scholes — {sheet_name}...")
        try:
            sheet_results['black_scholes'] = run_bs_analysis(
                prices, risk_free_rate=0.02
            )
            print(f"    ✓ Options pricées avec succès")
        except Exception as e:
            print(f"  ⚠ Black-Scholes échoué : {e}")

        # ── Monte Carlo Options ──────────────────────────────
        print(f"  Monte Carlo Options — {sheet_name}...")
        try:
            sheet_results['mc_options'] = run_mc_options_analysis(
                prices, risk_free_rate=0.02
            )
            print(f"    ✓ Options exotiques pricées")
        except Exception as e:
            print(f"  ⚠ MC Options échoué : {e}")
        # ── Modèle de Heston ─────────────────────────────────
        print(f"  Modèle de Heston — {sheet_name}...")
        try:
            sheet_results['heston'] = run_heston_analysis(
                prices, risk_free_rate=0.02
            )
            print(f"    ✓ Heston calibré avec succès")
        except Exception as e:
            print(f"  ⚠ Heston échoué : {e}")

        results[sheet_name] = sheet_results

    # ── Corrélation ──────────────────────────────────────────
    corr_matrix = calculate_correlation_matrix(dfs)
    if corr_matrix is not None:
        results['correlation_matrix'] = corr_matrix

    # ── Optimisation Portefeuille ─────────────────────────────
    if len([k for k in results.keys()
            if k != 'correlation_matrix']) >= 2:
        print("\n  Optimisation de portefeuille...")
        try:
            portfolio = run_portfolio_optimization(dfs)
            if portfolio:
                results['portfolio_optimization'] = portfolio
        except Exception as e:
            print(f"  ⚠ Optimisation portefeuille échouée : {e}")

    print(f"\n  Résultats générés pour : {list(results.keys())}")
    return results
if __name__ == "__main__":
    # Test rapide
    prices = pd.Series(
        np.random.randn(252).cumsum() + 100,
        index=pd.date_range(start='2024-01-01', periods=252)
    )
    metrics, returns = calculate_metrics(prices)
    print("=== TEST MÉTRIQUES ===")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")