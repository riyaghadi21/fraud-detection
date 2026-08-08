from risk_rules import label_risk, score_transaction


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_label_risk_boundaries():
    assert label_risk(29) == "low"
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"
    assert label_risk(60) == "high"


def test_large_amount_adds_risk():
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 1200,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    assert score_transaction(tx) >= 25


def base_tx(**overrides):
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 50,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    tx.update(overrides)
    return tx


def test_high_device_risk_increases_score():
    low = score_transaction(base_tx(device_risk_score=10))
    high = score_transaction(base_tx(device_risk_score=80))
    assert high > low


def test_international_increases_score():
    domestic = score_transaction(base_tx(is_international=0))
    international = score_transaction(base_tx(is_international=1))
    assert international > domestic


def test_high_velocity_increases_score():
    low = score_transaction(base_tx(velocity_24h=1))
    high = score_transaction(base_tx(velocity_24h=8))
    assert high > low


def test_prior_chargebacks_increase_score():
    none = score_transaction(base_tx(prior_chargebacks=0))
    many = score_transaction(base_tx(prior_chargebacks=2))
    assert many > none


def test_score_is_clamped_to_valid_range():
    lowest = score_transaction(base_tx())
    highest = score_transaction(
        base_tx(
            device_risk_score=90,
            is_international=1,
            amount_usd=5000,
            velocity_24h=10,
            failed_logins_24h=10,
            prior_chargebacks=5,
        )
    )
    assert 0 <= lowest <= 100
    assert 0 <= highest <= 100
    assert highest == 100


def test_known_fraud_pattern_scores_high():
    # Mirrors a real chargeback in the sample data: risky device, international,
    # high velocity, elevated failed logins.
    tx = base_tx(
        device_risk_score=85,
        is_international=1,
        velocity_24h=8,
        failed_logins_24h=7,
        amount_usd=1400,
    )
    assert label_risk(score_transaction(tx)) == "high"
