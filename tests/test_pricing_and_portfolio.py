"""
Unit tests for the Black-Scholes pricer (modules/black_scholes.py) and the
portfolio optimizer (modules/portfolio.py).

Run with:
    pytest tests/
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.black_scholes import (
    black_scholes_call,
    black_scholes_put,
    put_call_parity_check,
    implied_volatility,
    delta,
)
from modules.portfolio import minimum_variance_portfolio, maximum_sharpe_portfolio


def test_put_call_parity_holds():
    result = put_call_parity_check(S=100, K=105, T=1.0, r=0.03, sigma=0.25)
    assert result["parite_verifiee"]
    assert result["erreur"] < 1e-6


def test_call_price_increases_with_volatility():
    low_vol = black_scholes_call(S=100, K=100, T=1.0, r=0.02, sigma=0.10)
    high_vol = black_scholes_call(S=100, K=100, T=1.0, r=0.02, sigma=0.40)
    assert high_vol > low_vol


def test_deep_itm_call_delta_close_to_one():
    d = delta(S=200, K=50, T=0.5, r=0.02, sigma=0.20, option_type="call")
    assert d > 0.99


def test_implied_volatility_recovers_input_sigma():
    true_sigma = 0.28
    price = black_scholes_call(S=100, K=95, T=0.75, r=0.02, sigma=true_sigma)

    recovered = implied_volatility(price, S=100, K=95, T=0.75, r=0.02, option_type="call")

    assert recovered == pytest.approx(true_sigma, abs=1e-4)


def _synthetic_returns(n_assets=4, n_days=500, seed=3):
    rng = np.random.default_rng(seed)
    mean_returns = rng.uniform(0.0002, 0.0008, n_assets)
    A = rng.normal(0, 0.01, (n_assets, n_assets))
    cov_matrix = A @ A.T + np.eye(n_assets) * 1e-5  # symmetric positive-definite
    return mean_returns, cov_matrix


def test_minimum_variance_portfolio_weights_sum_to_one():
    mean_returns, cov_matrix = _synthetic_returns()
    result = minimum_variance_portfolio(mean_returns, cov_matrix)

    assert result is not None
    assert result["weights"].sum() == pytest.approx(1.0, abs=1e-6)
    assert (result["weights"] >= -1e-8).all()


def test_maximum_sharpe_portfolio_has_at_least_min_variance_sharpe():
    mean_returns, cov_matrix = _synthetic_returns()

    minvar = minimum_variance_portfolio(mean_returns, cov_matrix)
    maxsharpe = maximum_sharpe_portfolio(mean_returns, cov_matrix, risk_free_rate=0.02)

    assert maxsharpe["sharpe"] >= minvar["sharpe"] - 1e-6
