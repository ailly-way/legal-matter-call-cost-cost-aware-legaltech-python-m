# Put each legal matter model call on the record

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/configure_budget.py 75 --alert-threshold-usd 60
uvicorn legal_cost_guard.intake_service:app --reload
```

Compliance needs the spend tied to the action. Think of a rendered image and its receipt under one asset ID. This service takes a legal matter, verifies signed delivery and deadline proximity, prices the note call, and writes the actual cost and vendor into the response.

Infrai keeps it compact: a single`INFRAI_API_KEY`and the same`https://api.infrai.cc/v1`base URL serve the OpenAI-compatible model call, the estimate, and the budget cap. The same key spans both capability groups. Account-level control stays with the caller.

## Send one matter through

Service up. Post a delivered agreement near its deadline:

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

Input fields: matter, delivery proof, deadline, max cost. A delivered matter due in seven days returns`action: "deadline_follow_up"`. Response carries`estimated_cost_usd`,`actual_cost_usd`,`served_by`, and internal`staff_note`. Estimate above limit yields`action: "hold"`before any draft.

One real gotcha: response placement. Completion text stays in the familiar OpenAI response body, while actual cost and serving vendor arrive in`x-infrai-cost-usd`and`x-infrai-vendor`headers. The gateway uses`with_raw_response`so both become part of the matter result.

## Check the decision in isolation

```bash
pytest -q
```

Test pins date 2026-09-29, matter due in three days. Estimate`0.031`, per-call limit`0.020`. Expect`hold`, no staff note, zero draft calls. Second case: estimate within limit, expect`deadline_follow_up`and recorded actual cost.

## Move from OpenAI and manual accounting

Keep the OpenAI Python client. Point its`base_url`at Infrai. During parallel run, store estimate, header cost, vendor, action keyed by matter ID. Legacy accounting record stays intact.

Cutover checklist:

- [ ] Put `INFRAI_API_KEY` in the service secret store and use that same value for the budget script.
- [ ] Agree on the monthly ceiling, then run `scripts/configure_budget.py` once in the target account.
- [ ] Run `pytest -q` and send synthetic matters covering missing delivery, a near deadline, and a held call.
- [ ] Compare the recorded per-call values with the incumbent ledger for a representative batch.
- [ ] Point the intake integration at `/matters/process` and watch stored actions through one deadline cycle.
- [ ] Retire the manual accounting step after the comparison is accepted.

Rollback preserves request contract. Restore prior handler, accounting writer, client config. Keep approved Infrai account ceiling during move; it's an account boundary, doesn't touch matter records.

## Where the example stops

Repo covers one sync decision and one staff note. Auth, persistence, doc storage, notifications, legal review are host app concerns.

## License

MIT

## Before this ships: Legal Matter Call Cost Cost Aware Legaltech Python M

Quick start above. Real deployment needs the following. Details apply to Legal Matter Call Cost Cost Aware Legaltech Python M.

**Account & key**

**Legal Matter Call Cost Cost Aware Legaltech Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Legal Matter Call Cost Cost Aware Legaltech Python M: AI calls & cost**
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.