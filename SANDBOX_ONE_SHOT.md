# One-shot Sandbox draft validation

This opt-in workflow is a synthetic transport test. It uses the exact public ScopeProof v0.3.4 source commit `5af9f89a780ea265f76fef26d9b9614b93d46f4f`, authenticates to PayPal **Sandbox**, creates one **unsent** EUR 125 draft, reads it back, and verifies its fields. It does not send an invoice, capture a payment, run fresh AI inference, or prove a real customer's approval or the browser UI.

Before the **first** manual dispatch on `main`, create the GitHub Actions environment `scopeproof-sandbox-validation` and confirm that it has all four environment-scoped secrets, without revealing their values:

| Secret | Value |
| --- | --- |
| `PAYPAL_SANDBOX_CLIENT_ID` | Client ID of the Sandbox app with Invoicing enabled |
| `PAYPAL_SANDBOX_CLIENT_SECRET` | Matching Sandbox app secret |
| `PAYPAL_SANDBOX_SELLER_EMAIL` | Generated Sandbox business test-account email for that app |
| `PAYPAL_SANDBOX_BUYER_EMAIL` | Distinct generated Sandbox personal test-account email |

Run the local checks before publishing or dispatching:

```sh
python3 -m unittest discover -s tools -p 'test_sandbox_once.py'
python3 run_tests.py
node test_ui_unsaved.js
```

Dispatch `.github/workflows/scopeproof-sandbox-once.yml` only after reviewing the exact published commit. The preflight has no Sandbox secrets: it requires the first workflow run, first attempt, and GitHub Actions API history containing only that current run. An unavailable/delayed API response, a missing secret, a cancelled run, or any failure **consumes the first attempt**. Do not rerun or dispatch a replacement to resolve an uncertain outcome. The runner's private SQLite ledger and signing key are ephemeral and are never published or uploaded; the public receipt omits credentials, emails, invoice ID, and billing key.

If the result is `UNKNOWN`, cancelled after the POST, or otherwise unclear, investigate **read-only** in the Sandbox business dashboard using the test seller, date, amount, and the deterministic synthetic invoice number derived from `PROJECT_ID` in `tools/sandbox_once.py`. A lost runner cannot reconcile automatically. GitHub run-history deletion or workflow recreation can defeat the cross-run guard; this is not a provider-level exactly-once guarantee.
