# modules/backtesting.py
import numpy as np
import pandas as pd

def momentum_strategy(prices, lookback=20, holding=5):
    """
    Stratégie Momentum :
    - Acheter si le prix a monté sur les 'lookback' derniers jours
    - Vendre si le prix a baissé
    - Conserver pendant 'holding' jours
    """
    returns = prices.pct_change().dropna()
    signals = pd.Series(0, index=prices.index)

    for i in range(lookback, len(prices)):
        past_return = (prices.iloc[i] / prices.iloc[i - lookback]) - 1
        if past_return > 0:
            signals.iloc[i] = 1   # Long
        elif past_return < 0:
            signals.iloc[i] = -1  # Short

    # Appliquer le signal avec délai holding
    position = signals.shift(1).fillna(0)
    strategy_returns = position * returns

    return signals, strategy_returns

def mean_reversion_strategy(prices, window=20, threshold=1.5):
    """
    Stratégie Mean-Reversion (Bollinger Bands) :
    - Acheter si prix < moyenne - threshold * std
    - Vendre si prix > moyenne + threshold * std
    """
    returns = prices.pct_change().dropna()
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()

    upper = rolling_mean + threshold * rolling_std
    lower = rolling_mean - threshold * rolling_std

    signals = pd.Series(0, index=prices.index)
    for i in range(window, len(prices)):
        if prices.iloc[i] < lower.iloc[i]:
            signals.iloc[i] = 1   # Acheter (prix bas)
        elif prices.iloc[i] > upper.iloc[i]:
            signals.iloc[i] = -1  # Vendre (prix haut)
        else:
            signals.iloc[i] = signals.iloc[i-1]  # Maintenir position

    position = signals.shift(1).fillna(0)
    strategy_returns = position * returns

    return signals, strategy_returns

def moving_average_crossover(prices, short_window=20, long_window=50):
    """
    Stratégie Moving Average Crossover :
    - Acheter quand SMA courte croise SMA longue par le haut
    - Vendre quand SMA courte croise SMA longue par le bas
    """
    returns = prices.pct_change().dropna()
    sma_short = prices.rolling(short_window).mean()
    sma_long = prices.rolling(long_window).mean()

    signals = pd.Series(0, index=prices.index)
    for i in range(long_window, len(prices)):
        if sma_short.iloc[i] > sma_long.iloc[i]:
            signals.iloc[i] = 1   # Long
        elif sma_short.iloc[i] < sma_long.iloc[i]:
            signals.iloc[i] = -1  # Short

    position = signals.shift(1).fillna(0)
    strategy_returns = position * returns

    return signals, strategy_returns

def compute_backtest_metrics(strategy_returns, benchmark_returns=None,
                              risk_free_rate=0.02):
    """Calcule les métriques de performance du backtest"""
    strategy_returns = strategy_returns.dropna()

    if len(strategy_returns) == 0:
        return {}

    # Rendements cumulatifs
    cumulative = (1 + strategy_returns).cumprod()

    # Métriques de base
    total_return = float((cumulative.iloc[-1] - 1) * 100)
    annual_return = float(strategy_returns.mean() * 252 * 100)
    volatility = float(strategy_returns.std() * np.sqrt(252) * 100)

    # Sharpe
    excess = strategy_returns.mean() - risk_free_rate / 252
    sharpe = float((excess / strategy_returns.std()) * np.sqrt(252)) \
        if strategy_returns.std() != 0 else 0

    # Sortino
    downside = strategy_returns[strategy_returns < 0].std()
    sortino = float(
        (strategy_returns.mean() * 252 - risk_free_rate) /
        (downside * np.sqrt(252))
    ) if downside != 0 else 0

    # Max Drawdown
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min() * 100)

    # Win Rate
    win_rate = float((strategy_returns > 0).mean() * 100)

    # Calmar Ratio
    calmar = float(annual_return / abs(max_drawdown)) \
        if max_drawdown != 0 else 0

    # Nombre de trades
    n_trades = int((strategy_returns != 0).sum())

    metrics = {
        'rendement_total': total_return,
        'rendement_annualise': annual_return,
        'volatilite': volatility,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'calmar_ratio': calmar,
        'n_trades': n_trades,
    }

    # Alpha & Beta vs benchmark
    if benchmark_returns is not None:
        benchmark_returns = benchmark_returns.reindex(
            strategy_returns.index
        ).dropna()
        aligned = strategy_returns.reindex(benchmark_returns.index).dropna()
        if len(aligned) > 10 and benchmark_returns.std() != 0:
            cov = np.cov(aligned, benchmark_returns)[0][1]
            beta = float(cov / np.var(benchmark_returns))
            alpha = float(
                (aligned.mean() - beta * benchmark_returns.mean()) * 252 * 100
            )
            metrics['alpha'] = alpha
            metrics['beta'] = beta
            bench_total = float(
                (1 + benchmark_returns).cumprod().iloc[-1] - 1
            ) * 100
            metrics['rendement_benchmark'] = bench_total
            metrics['surperformance'] = total_return - bench_total

    return metrics

def run_all_strategies(prices, benchmark_returns=None):
    """Lance toutes les stratégies et compare les résultats"""
    results = {}

    # Buy & Hold (benchmark de référence)
    bh_returns = prices.pct_change().dropna()
    results['Buy & Hold'] = {
        'returns': bh_returns,
        'metrics': compute_backtest_metrics(bh_returns, benchmark_returns),
        'cumulative': (1 + bh_returns).cumprod(),
    }

    # Momentum
    if len(prices) >= 25:
        _, mom_returns = momentum_strategy(prices)
        mom_returns = mom_returns.reindex(bh_returns.index).fillna(0)
        results['Momentum (20j)'] = {
            'returns': mom_returns,
            'metrics': compute_backtest_metrics(
                mom_returns, benchmark_returns
            ),
            'cumulative': (1 + mom_returns).cumprod(),
        }

    # Mean Reversion
    if len(prices) >= 25:
        _, mr_returns = mean_reversion_strategy(prices)
        mr_returns = mr_returns.reindex(bh_returns.index).fillna(0)
        results['Mean Reversion'] = {
            'returns': mr_returns,
            'metrics': compute_backtest_metrics(
                mr_returns, benchmark_returns
            ),
            'cumulative': (1 + mr_returns).cumprod(),
        }

    # MA Crossover
    if len(prices) >= 55:
        _, mac_returns = moving_average_crossover(prices)
        mac_returns = mac_returns.reindex(bh_returns.index).fillna(0)
        results['MA Crossover (20/50)'] = {
            'returns': mac_returns,
            'metrics': compute_backtest_metrics(
                mac_returns, benchmark_returns
            ),
            'cumulative': (1 + mac_returns).cumprod(),
        }

    return results