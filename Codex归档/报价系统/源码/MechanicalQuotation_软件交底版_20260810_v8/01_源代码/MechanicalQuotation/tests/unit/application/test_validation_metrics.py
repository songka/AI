from quotation.application.validation_metrics import calculate_accuracy_metrics


def test_accuracy_metrics_and_exclusive_buckets():
    metrics = calculate_accuracy_metrics(
        [
            {"historical_price": 100, "system_price": 95},
            {"historical_price": 100, "system_price": 115},
            {"historical_price": 100, "system_price": 125},
            {"historical_price": 100, "system_price": 150},
        ]
    )

    assert metrics["wape_pct"] == 23.75
    assert metrics["mae_cny"] == 23.75
    assert metrics["median_absolute_deviation_cny"] == 20.0
    assert metrics["buckets"] == {
        "<=10%": 1,
        "10-20%": 1,
        "20-30%": 1,
        ">30%": 1,
    }
