"""Typed legal workflow and its deterministic follow-up decision."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal, Protocol

from pydantic import BaseModel, Field


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_reference: str = Field(min_length=1)
    matter_kind: str = Field(min_length=1)
    intake_summary: str = Field(min_length=1, max_length=4_000)
    signed_document_delivered_at: datetime | None = None
    deadline_on: date
    max_call_cost_usd: Decimal = Field(gt=0)


class MatterResult(BaseModel):
    matter_id: str
    action: Literal["confirm_delivery", "deadline_follow_up", "monitor", "hold"]
    days_to_deadline: int
    estimated_cost_usd: Decimal
    actual_cost_usd: Decimal | None = None
    served_by: str | None = None
    staff_note: str | None = None


class MatterGateway(Protocol):
    def estimate(self, messages: list[dict[str, str]], expected_output_tokens: int) -> Decimal:
        """Return the estimated USD amount for these messages."""

    def draft(self, messages: list[dict[str, str]], request_id: str) -> tuple[str, Decimal, str | None]:
        """Return the note, observed USD amount, and serving vendor."""


def choose_action(matter: MatterIntake, today: date) -> tuple[str, int]:
    days_to_deadline = (matter.deadline_on - today).days
    if matter.signed_document_delivered_at is None:
        return "confirm_delivery", days_to_deadline
    if days_to_deadline <= 7:
        return "deadline_follow_up", days_to_deadline
    return "monitor", days_to_deadline


class MatterWorkflow:
    def __init__(self, gateway: MatterGateway) -> None:
        self.gateway = gateway

    def process(self, matter: MatterIntake, today: date | None = None) -> MatterResult:
        current_date = today or datetime.now(timezone.utc).date()
        action, days_to_deadline = choose_action(matter, current_date)
        messages = _messages(matter, action, days_to_deadline)
        estimate = self.gateway.estimate(messages, expected_output_tokens=180)
        if estimate > matter.max_call_cost_usd:
            return MatterResult(
                matter_id=matter.matter_id,
                action="hold",
                days_to_deadline=days_to_deadline,
                estimated_cost_usd=estimate,
            )

        note, actual_cost, served_by = self.gateway.draft(
            messages, request_id=f"matter-note-{matter.matter_id}-{action}"
        )
        return MatterResult(
            matter_id=matter.matter_id,
            action=action,
            days_to_deadline=days_to_deadline,
            estimated_cost_usd=estimate,
            actual_cost_usd=actual_cost,
            served_by=served_by,
            staff_note=note,
        )


def _messages(matter: MatterIntake, action: str, days_to_deadline: int) -> list[dict[str, str]]:
    delivery = (
        matter.signed_document_delivered_at.isoformat()
        if matter.signed_document_delivered_at
        else "not recorded"
    )
    return [
        {
            "role": "system",
            "content": (
                "Draft a concise internal legal-operations note. Use only the supplied facts, "
                "state the next action, and do not provide legal advice."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Matter: {matter.matter_id}\nClient reference: {matter.client_reference}\n"
                f"Type: {matter.matter_kind}\nIntake: {matter.intake_summary}\n"
                f"Signed document delivered: {delivery}\nDeadline: {matter.deadline_on.isoformat()}\n"
                f"Days remaining: {days_to_deadline}\nRequired action: {action}"
            ),
        },
    ]
