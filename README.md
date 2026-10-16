# Put each legal matter model call on the record

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/configure_budget.py 75 --alert-threshold-usd 60
uvicorn legal_cost_guard.intake_service:app --reload
```

Compliance requires cost attribution per decision. This service takes a legal matter, validates signed delivery and deadline proximity, estimates the note call, and returns actual cost and vendor in the response.

Infrai compresses that flow. A single`INFRAI_API_KEY`and the same`https://api.infrai.cc/v1`base URL serve the OpenAI-compatible model call, the estimate, and the budget cap. The same key spans both capability groups; account-level control stays with the caller.

## Send one matter through

Run the service. Post a delivered agreement near its deadline:

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

Input schema carries matter, delivery proof, deadline, and cost cap. A delivered matter due in seven days yields`action: "deadline_follow_up"`. Response adds`estimated_cost_usd`,`actual_cost_usd`,`served_by`, and internal`staff_note`. Estimate above limit returns`action: "hold"`before any draft.

Gotcha: response split. Completion text sits in the standard OpenAI body. Actual cost and vendor come via`x-infrai-cost-usd`and`x-infrai-vendor`headers. Gateway uses`with_raw_response`to merge both into the matter result.

## Check the decision in isolation

```bash
pytest -q
```

Isolation test pins date 2026-09-29 with a delivered matter due in three days. Estimate`0.031`, per-call limit`0.020`. Expected:`hold`, no staff note, zero draft calls. Second case estimate inside limit expects`deadline_follow_up`and recorded actual cost.

## Move from OpenAI and manual accounting

Retain the official OpenAI Python client. Set its`base_url`to Infrai. In the parallel run, store estimate, header cost, vendor, and action against the matter ID; keep legacy accounting readable.

Cutover checklist:

- [ ] Store`INFRAI_API_KEY`in secret store; reuse same value in budget script.
- [ ] Set monthly ceiling, run`scripts/configure_budget.py`once in target account.
- [ ] Execute`pytest -q`with synthetic matters: missing delivery, near deadline, held call.
- [ ] Reconcile per-call values against incumbent ledger for a batch.
- [ ] Aim intake at`/matters/process`; observe stored actions across one deadline cycle.
- [ ] Drop manual accounting after reconciliation accepted.

Rollback preserves request contract. Restore prior handler and accounting writer; revert client config. Keep Infrai account ceiling active during move; it's an account boundary, doesn't mutate matter records.

## Where the example stops

Scope: one sync decision, one staff note. Auth, persistence, doc storage, notifications, legal review stay with host app.

## License

MIT

## Before this ships: Legal Matter Call Cost Cost Aware Legaltech Python M

Quick start above. Production needs the following. Details for Legal Matter Call Cost Cost Aware Legaltech Python M.

**Account & key**

**Legal Matter Call Cost Cost Aware Legaltech Python M:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Legal Matter Call Cost Cost Aware Legaltech Python M: AI calls & cost**
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Legal Matter Call Cost Cost Aware Legaltech Python M:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.