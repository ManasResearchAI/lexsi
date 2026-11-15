from ticket_system.metrics import evaluate_records


def test_metrics_only_score_labelled_fields():
    metrics = evaluate_records([{
        "language": "yor",
        "target": {"language": "yor", "sentiment": "positive"},
        "prediction": {"language": "yor", "sentiment": "positive"},
    }])
    assert metrics["language_accuracy"] == 1
    assert metrics["sentiment_accuracy"] == 1
    assert metrics["sentiment_macro_f1"] == 1
    assert "intent_accuracy" not in metrics


def test_entity_f1_and_pii_recall():
    metrics = evaluate_records([{
        "language": "swa",
        "target": {"entities": [{"type": "PER", "text": "Asha"}]},
        "prediction": {"entities": [{"type": "PER", "text": "Asha"}]},
    }])
    assert metrics["entity_f1"] == 1
    assert metrics["pii_recall"] == 1


def test_malformed_entities_fail_scoring_without_crashing():
    metrics = evaluate_records([{
        "language": "yor",
        "target": {"entities": [{"type": "PER", "text": "Ada"}]},
        "prediction": {"entities": [{"type": "PER"}, "bad"]},
    }])
    assert metrics["entity_recall"] == 0
    assert metrics["schema_valid_rate"] == 0

