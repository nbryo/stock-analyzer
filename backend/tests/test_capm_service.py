import math
from app.services.capm_service import (
    calc_beta,
    calc_alpha,
    calc_sharpe,
    calc_capm_metrics,
    calc_expected_return,
)


def test_calc_beta_positive_correlation():
    """Stock that moves with the market should have beta > 0."""
    stock = [0.01, 0.02, -0.01, 0.03, 0.015, -0.005, 0.02]
    market = [0.008, 0.015, -0.008, 0.025, 0.01, -0.003, 0.018]
    beta = calc_beta(stock, market)
    assert 0.5 < beta < 2.0, f"Beta {beta} out of expected range"


def test_calc_alpha_positive():
    """Stock outperforming CAPM prediction should have positive alpha."""
    actual_return = 0.15  # 15%
    rf = 0.04
    beta = 1.2
    market_return = 0.10
    alpha = calc_alpha(actual_return, rf, beta, market_return)
    # expected = 0.04 + 1.2 * (0.10 - 0.04) = 0.112
    # alpha = 0.15 - 0.112 = 0.038
    assert alpha > 0, f"Alpha {alpha} should be positive"
    assert abs(alpha - 0.038) < 0.001


def test_calc_capm_metrics_full():
    """Full CAPM metrics should return all expected keys with reasonable values."""
    # Simulate 53 weeks of prices (gives 52 weekly returns)
    stock_prices = [100 + i * 0.5 + (i % 3 - 1) * 0.3 for i in range(53)]
    market_prices = [3000 + i * 10 + (i % 4 - 2) * 5 for i in range(53)]
    rf = 0.0435

    result = calc_capm_metrics(stock_prices, market_prices, rf)

    assert "beta" in result
    assert "alpha" in result
    assert "sharpe" in result
    assert "treynor" in result
    assert "r_squared" in result
    assert "volatility" in result
    assert 0 <= result["r_squared"] <= 1.0
    assert result["volatility"] >= 0
