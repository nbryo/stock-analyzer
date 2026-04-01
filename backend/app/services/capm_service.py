"""CAPM calculation functions using NumPy/SciPy."""

import math

import numpy as np
from scipy import stats


def calc_beta(stock_returns: list[float], market_returns: list[float]) -> float:
    """Calculate beta via OLS regression of stock returns on market returns.

    Beta = slope of the regression line (stock ~ market).
    """
    if len(stock_returns) < 2 or len(market_returns) < 2:
        return 1.0
    slope, _intercept, _r, _p, _se = stats.linregress(market_returns, stock_returns)
    return round(slope, 4)


def calc_alpha(
    actual_return: float,
    rf: float,
    beta: float,
    market_return: float,
) -> float:
    """Calculate Jensen's alpha.

    alpha = actual_return - (rf + beta * (market_return - rf))
    """
    expected = rf + beta * (market_return - rf)
    return round(actual_return - expected, 4)


def calc_sharpe(returns: list[float], rf: float) -> float:
    """Calculate annualized Sharpe ratio from weekly returns.

    sharpe = (mean(returns) - rf_weekly) / std(returns) * sqrt(52)
    """
    if len(returns) < 2:
        return 0.0
    arr = np.array(returns)
    rf_weekly = rf / 52
    excess_mean = arr.mean() - rf_weekly
    std = arr.std(ddof=1)
    if std == 0:
        return 0.0
    return round(float(excess_mean / std * math.sqrt(52)), 4)


def calc_expected_return(rf: float, beta: float, market_return: float) -> float:
    """CAPM expected return = rf + beta * (market_return - rf)."""
    return round(rf + beta * (market_return - rf), 4)


def calc_capm_metrics(
    stock_weekly_prices: list[float],
    market_weekly_prices: list[float],
    rf_rate: float,
) -> dict:
    """Calculate all CAPM metrics from weekly price series.

    Args:
        stock_weekly_prices: Weekly closing prices (oldest first).
        market_weekly_prices: Weekly closing prices for market index (oldest first).
        rf_rate: Annual risk-free rate as decimal (e.g. 0.0435 for 4.35%).

    Returns:
        Dict with beta, alpha, sharpe, treynor, r_squared, volatility.
    """
    if len(stock_weekly_prices) < 3 or len(market_weekly_prices) < 3:
        return {
            "beta": 1.0,
            "alpha": 0.0,
            "sharpe": 0.0,
            "treynor": 0.0,
            "r_squared": 0.0,
            "volatility": 0.0,
        }

    stock_prices = np.array(stock_weekly_prices)
    market_prices = np.array(market_weekly_prices)

    # Weekly returns
    stock_returns = np.diff(stock_prices) / stock_prices[:-1]
    market_returns = np.diff(market_prices) / market_prices[:-1]

    # Ensure same length
    min_len = min(len(stock_returns), len(market_returns))
    stock_returns = stock_returns[-min_len:]
    market_returns = market_returns[-min_len:]

    # Beta & R-squared via regression
    slope, intercept, r_value, _p, _se = stats.linregress(
        market_returns, stock_returns
    )
    beta = round(float(slope), 4)
    r_squared = round(float(r_value**2), 4)

    # Annualized returns
    stock_annual = float((1 + stock_returns.mean()) ** 52 - 1)
    market_annual = float((1 + market_returns.mean()) ** 52 - 1)

    # Alpha
    alpha = calc_alpha(stock_annual, rf_rate, beta, market_annual)

    # Sharpe
    sharpe = calc_sharpe(stock_returns.tolist(), rf_rate)

    # Treynor
    treynor = 0.0
    if beta != 0:
        treynor = round((stock_annual - rf_rate) / beta, 4)

    # Annualized volatility
    volatility = round(float(stock_returns.std(ddof=1) * math.sqrt(52)), 4)

    return {
        "beta": beta,
        "alpha": alpha,
        "sharpe": sharpe,
        "treynor": treynor,
        "r_squared": r_squared,
        "volatility": volatility,
    }
