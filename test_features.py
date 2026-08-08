import pandas as pd

from features import build_model_frame


def test_build_model_frame_keeps_every_transaction():
    transactions = pd.DataFrame(
        [
            {"transaction_id": 1, "account_id": 1, "amount_usd": 10.0, "failed_logins_24h": 0},
            {"transaction_id": 2, "account_id": 999, "amount_usd": 20.0, "failed_logins_24h": 0},
        ]
    )
    accounts = pd.DataFrame([{"account_id": 1, "prior_chargebacks": 0}])

    result = build_model_frame(transactions, accounts)

    assert len(result) == len(transactions)
    unmatched = result.loc[result["transaction_id"] == 2, "prior_chargebacks"]
    assert unmatched.isna().all()


def test_is_large_amount_threshold():
    transactions = pd.DataFrame(
        [
            {"transaction_id": 1, "account_id": 1, "amount_usd": 999.99, "failed_logins_24h": 0},
            {"transaction_id": 2, "account_id": 1, "amount_usd": 1000.0, "failed_logins_24h": 0},
        ]
    )
    accounts = pd.DataFrame([{"account_id": 1, "prior_chargebacks": 0}])

    result = build_model_frame(transactions, accounts).set_index("transaction_id")

    assert result.loc[1, "is_large_amount"] == 0
    assert result.loc[2, "is_large_amount"] == 1


def test_login_pressure_buckets():
    transactions = pd.DataFrame(
        [
            {"transaction_id": 1, "account_id": 1, "amount_usd": 10.0, "failed_logins_24h": 0},
            {"transaction_id": 2, "account_id": 1, "amount_usd": 10.0, "failed_logins_24h": 2},
            {"transaction_id": 3, "account_id": 1, "amount_usd": 10.0, "failed_logins_24h": 5},
        ]
    )
    accounts = pd.DataFrame([{"account_id": 1, "prior_chargebacks": 0}])

    result = build_model_frame(transactions, accounts).set_index("transaction_id")

    assert result.loc[1, "login_pressure"] == "none"
    assert result.loc[2, "login_pressure"] == "low"
    assert result.loc[3, "login_pressure"] == "high"
