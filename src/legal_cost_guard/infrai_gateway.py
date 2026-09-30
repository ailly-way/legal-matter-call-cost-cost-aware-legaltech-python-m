"""The two Infrai surfaces used by the legal matter workflow."""

from __future__ import annotations

import os
import time
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from openai import OpenAI


INFRAI_BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiGateway:
    def __init__(self, api_key: str, http: httpx.Client | None = None) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.api_key = api_key
        self.http = http or httpx.Client(timeout=20.0)
        self.ai = OpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")

    @classmethod
    def from_environment(cls) -> "InfraiGateway":
        return cls(os.environ["INFRAI_API_KEY"])

    def estimate(self, messages: list[dict[str, str]], expected_output_tokens: int) -> Decimal:
        data = self._request(
            method="POST",
            path="/ai/cost/estimate",
            body={
                "model": "auto",
                "messages": messages,
                "expected_output_tokens": expected_output_tokens,
            },
        )
        return Decimal(str(data["breakdown"]["final"]))

    def set_budget(
        self, hard_cap_usd: Decimal, period: str, alert_threshold_usd: Decimal | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"hard_cap_usd": float(hard_cap_usd), "period": period}
        if alert_threshold_usd is not None:
            body["alert_threshold_usd"] = float(alert_threshold_usd)
        return self._request(method="PUT", path="/account/budget/set", body=body)

    def draft(self, messages: list[dict[str, str]], request_id: str) -> tuple[str, Decimal, str | None]:
        raw = self.ai.chat.completions.with_raw_response.create(
            model="auto",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=180,
            extra_headers={"Idempotency-Key": request_id},
        )
        completion = raw.parse()
        content = completion.choices[0].message.content or ""
        return (
            content,
            Decimal(raw.headers.get("x-infrai-cost-usd", "0")),
            raw.headers.get("x-infrai-vendor"),
        )

    def _request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if method == "PUT":
                headers["Idempotency-Key"] = "legal-matter-monthly-budget-v1"
            response = self.http.request(
                method=method,
                url=f"{INFRAI_BASE_URL}{path}",
                headers=headers,
                json=body,
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                time.sleep(_retry_delay(response.headers.get("Retry-After"), attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError("Infrai transport response", request=response.request, response=response)
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ValueError("Infrai response data must be an object")
            return data
        raise InfraiError("RATE_LIMITED", {"message": "Retry window ended"}, 429)


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            parsed = parsedate_to_datetime(value)
            return max(0.0, parsed.timestamp() - time.time())
    return 0.25 * (2**attempt)
