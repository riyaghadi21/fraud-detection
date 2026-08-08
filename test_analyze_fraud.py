import pandas as pd
import pytest

from analyze_fraud import score_transactions, summarize_results


def make_scored_frame():
    return pd.DataFrame(
        [
            {"transaction_id": 1, "risk_label": "low", "amount_usd": 100.0},
            {"transaction_id": 2, "risk_label": "low", "amount_usd": 50.0},
            {"transaction_id": 3, "risk_label": "medium", "amount_usd": 200.0},
            {"transaction_id": 4, "risk_label": "high", "amount_usd": 1000.0},
            {"transaction_id": 5, "risk_label": "high", "amount_usd": 500.0},
        ]
    )


def test_summarize_results_aggregates_amounts_correctly():
    scored = make_scored_frame()
    chargebacks = pd.DataFrame({"transaction_id": []})

    summary = summarize_results(scored, chargebacks).set_index("risk_label")

    assert summary.loc["low", "transactions"] == 2
    assert summary.loc["low", "total_amount_usd"] == pytest.approx(150.0)
    assert summary.loc["low", "avg_amount_usd"] == pytest.approx(75.0)


def test_summarize_results_chargeback_rate_is_zero_with_no_fraud():
    scored = make_scored_frame()
    chargebacks = pd.DataFrame({"transaction_id": []})

    summary = summarize_results(scored, chargebacks)

    assert not summary["chargeback_rate"].isna().any()
    assert (summary["chargeback_rate"] == 0).all()


def test_summarize_results_chargeback_rate_reflects_known_fraud():
    scored = make_scored_frame()
    chargebacks = pd.DataFrame({"transaction_id": [4]})  # one of the two "high" txns

    summary = summarize_results(scored, chargebacks).set_index("risk_label")

    assert summary.loc["high", "chargebacks"] == 1
    assert summary.loc["high", "chargeback_rate"] == pytest.approx(0.5)


def test_summarize_results_orders_chargeback_rate_with_risk_label():
    # Business invariant: higher risk labels should carry equal or higher
    # real fraud rates. This is what the earlier scoring-sign fix restored.
    scored = make_scored_frame()
    chargebacks = pd.DataFrame({"transaction_id": [4]})

    summary = summarize_results(scored, chargebacks).set_index("risk_label")

    assert summary.loc["low", "chargeback_rate"] <= summary.loc["medium", "chargeback_rate"]
    assert summary.loc["medium", "chargeback_rate"] <= summary.loc["high", "chargeback_rate"]


def test_summarize_results_does_not_double_count_repeat_chargeback_records():
    # A single transaction can appear more than once in chargebacks.csv
    # (e.g. a re-dispute). The rate must reflect distinct fraudulent
    # transactions, not the number of chargeback events.
    scored = make_scored_frame()
    chargebacks = pd.DataFrame({"transaction_id": [4, 4]})

    summary = summarize_results(scored, chargebacks).set_index("risk_label")

    assert summary.loc["high", "chargebacks"] == 1
    assert summary.loc["high", "chargeback_rate"] <= 1.0


def test_score_transactions_adds_risk_columns():
    transactions = pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "account_id": 1,
                "amount_usd": 50.0,
                "device_risk_score": 5,
                "is_international": 0,
                "velocity_24h": 1,
                "failed_logins_24h": 0,
            }
        ]
    )
    accounts = pd.DataFrame([{"account_id": 1, "prior_chargebacks": 0}])

    scored = score_transactions(transactions, accounts)

    assert "risk_score" in scored.columns
    assert "risk_label" in scored.columns
    assert scored.loc[0, "risk_label"] == "low"
