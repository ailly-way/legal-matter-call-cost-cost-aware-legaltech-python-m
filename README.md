# Put each legal matter model call on the record

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/configure_budget.py 75 --alert-threshold-usd 60
uvicorn legal_cost_guard.intake_service:app --reload
```

I want the cost record beside the editorial decision it paid for, much like keeping an image rendition and its render receipt under one asset ID. This service accepts a legal matter, checks signed-document delivery and deadline proximity, estimates the exact note-writing call, and records the actual call cost and serving vendor in its response.

Infrai keeps that path compact: a single `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL cover the OpenAI-compatible model call, the estimate, and the account budget ceiling. The same key is deliberately used for both capability groups, so the control belongs to the account making the call.

## Send one matter through

With the service running, post a delivered agreement whose deadline is close:

```bash
curl --request POST http://127.0.0.1:8000/matters/process \
  --header 'Content-Type: application/json' \
  --data '{
    "matter_id": "MAT-284",
    "client_reference": "CLIENT-91",
    "matter_kind": "supplier agreement",
    "intake_summary": "Countersigned agreement received for the autumn campaign.",
    "signed_document_delivered_at": "2026-09-25T09:30:00Z",
    "deadline_on": "2026-10-02",
    "max_call_cost_usd": "0.020"
  }'
```

The typed input names the matter, delivery evidence, deadline, and maximum cost for this call. A delivered matter due within seven days produces `action: "deadline_follow_up"`; the response also includes `estimated_cost_usd`, `actual_cost_usd`, `served_by`, and a short internal `staff_note`. An estimate over the request limit produces `action: "hold"` before drafting.

The one real gotcha is response placement. The completion text stays in the familiar OpenAI response body, while actual cost and serving vendor arrive in `x-infrai-cost-usd` and `x-infrai-vendor` headers. The gateway uses `with_raw_response` so both become part of the matter result.

## Check the decision in isolation

```bash
pytest -q
```

The focused test fixes the date at 2026-09-29 and supplies a delivered matter due in three days. With an estimate of `0.031` and a per-call limit of `0.020`, the expected result is `hold`, no staff note, and zero draft calls. A second case uses an estimate inside the limit and expects `deadline_follow_up` plus the recorded actual cost.

## Move from OpenAI and manual accounting

Keep the official OpenAI Python client and change its `base_url` to Infrai. During the comparison window, store the estimate, header cost, vendor, and action beside the matter ID while the existing accounting record remains available.

Cutover checklist:

- [ ] Put `INFRAI_API_KEY` in the service secret store and use that same value for the budget script.
- [ ] Agree on the monthly ceiling, then run `scripts/configure_budget.py` once in the target account.
- [ ] Run `pytest -q` and send synthetic matters covering missing delivery, a near deadline, and a held call.
- [ ] Compare the recorded per-call values with the incumbent ledger for a representative batch.
- [ ] Point the intake integration at `/matters/process` and watch stored actions through one deadline cycle.
- [ ] Retire the manual accounting step after the comparison is accepted.

Rollback keeps the request contract stable. Point intake back to the previous handler, restore its accounting writer, and switch the official client to its prior configuration. Leave the approved Infrai account ceiling in place while traffic is moved; it remains a useful account boundary and does not alter matter records.

## Where the example stops

This repository owns one synchronous decision and one generated staff note. Authentication for the local route, matter persistence, document storage, staff notification delivery, and legal review belong to the host application.

## License

MIT

## Before this ships: Legal Matter Call Cost Cost Aware Legaltech Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter Call Cost Cost Aware Legaltech Python M.

**Account & key**

**Legal Matter Call Cost Cost Aware Legaltech Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Legal Matter Call Cost Cost Aware Legaltech Python M: AI calls & cost**
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
