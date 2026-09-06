# modules/rolling_metrics.py
import pandas as pd
import numpy as np

def rolling_sharpe(returns, window=30, risk_free_rate=0.02):
    """Sharpe Ratio glissant"""
    rolling_mean = returns.rolling(window).mean()
    rolling_std = returns.rolling(window).std()
    excess = rolling_mean - risk_free_rate / 252
    sharpe = (excess / rolling_std) * np.sqrt(252)
    sharpe.name = f'Sharpe_{window}j'
    return sharpe

def rolling_volatility(returns, window=30):
    """Volatilité glissante annualisée"""
    vol = returns.rolling(window).std() * np.sqrt(252) * 100
    vol.name = f'Vol_{window}j'
    return vol

def rolling_drawdown(returns):
    """Drawdown glissant"""
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max * 100
    drawdown.name = 'Drawdown'
    return drawdown

def rolling_beta(returns, market_returns, window=60):
    """Beta glissant par rapport au marché"""
    betas = []
    for i in range(window, len(returns)):
        r = returns.iloc[i-window:i]
        m = market_returns.iloc[i-window:i]
        if len(r) == len(m) and m.std() != 0:
            cov = np.cov(r, m)[0][1]
            var = np.var(m)
            betas.append(cov / var)
        else:
            betas.append(np.nan)
    beta_series = pd.Series(
        [np.nan] * window + betas,
        index=returns.index,
        name='Beta_glissant'
    )
    return beta_series

def rolling_sortino(returns, window=30, risk_free_rate=0.02):
    """Sortino Ratio glissant"""
    results = []
    for i in range(window, len(returns)):
        r = returns.iloc[i-window:i]
        mean_r = r.mean() * 252
        downside = r[r < 0].std() * np.sqrt(252)
        if downside != 0:
            sortino = (mean_r - risk_free_rate) / downside
        else:
            sortino = np.nan
        results.append(sortino)

    sortino_series = pd.Series(
        [np.nan] * window + results,
        index=returns.index,
        name=f'Sortino_{window}j'
    )
    return sortino_series

def compute_all_rolling(returns, windows=[30, 60, 90]):
    """Calcule toutes les métriques glissantes"""
    result = {}

    for w in windows:
        result[f'sharpe_{w}j'] = rolling_sharpe(returns, window=w)
        result[f'volatilite_{w}j'] = rolling_volatility(returns, window=w)
        result[f'sortino_{w}j'] = rolling_sortino(returns, window=w)

    result['drawdown'] = rolling_drawdown(returns)

    return result