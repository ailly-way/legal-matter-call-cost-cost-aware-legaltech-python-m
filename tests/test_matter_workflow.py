from datetime import date, datetime, timezone
from decimal import Decimal

from legal_cost_guard.matter_workflow import MatterIntake, MatterWorkflow


class RecordingGateway:
    def __init__(self, estimate: str) -> None:
        self.estimate_value = Decimal(estimate)
        self.draft_calls = 0

    def estimate(self, messages: list[dict[str, str]], expected_output_tokens: int) -> Decimal:
        assert "Required action: deadline_follow_up" in messages[1]["content"]
        assert expected_output_tokens == 180
        return self.estimate_value

    def draft(self, messages: list[dict[str, str]], request_id: str) -> tuple[str, Decimal, str]:
        self.draft_calls += 1
        return "Contact the filing team today.", Decimal("0.0042"), "example-vendor"


def delivered_matter(maximum: str = "0.020") -> MatterIntake:
    return MatterIntake(
        matter_id="MAT-284",
        client_reference="CLIENT-91",
        matter_kind="supplier agreement",
        intake_summary="Countersigned agreement received for the autumn campaign.",
        signed_document_delivered_at=datetime(2026, 9, 25, 9, 30, tzinfo=timezone.utc),
        deadline_on=date(2026, 10, 2),
        max_call_cost_usd=Decimal(maximum),
    )


def test_due_matter_is_held_before_drafting_when_estimate_crosses_limit() -> None:
    gateway = RecordingGateway("0.031")

    result = MatterWorkflow(gateway).process(delivered_matter(), today=date(2026, 9, 29))

    assert result.action == "hold"
    assert result.days_to_deadline == 3
    assert result.estimated_cost_usd == Decimal("0.031")
    assert result.staff_note is None
    assert gateway.draft_calls == 0


def test_due_delivered_matter_gets_a_follow_up_note() -> None:
    gateway = RecordingGateway("0.003")

    result = MatterWorkflow(gateway).process(delivered_matter(), today=date(2026, 9, 29))

    assert result.action == "deadline_follow_up"
    assert result.actual_cost_usd == Decimal("0.0042")
    assert result.staff_note == "Contact the filing team today."
    assert gateway.draft_calls == 1
