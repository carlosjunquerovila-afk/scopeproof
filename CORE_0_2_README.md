# ScopeProof — integration candidate 0.2.0

**A controlled bridge from reviewed deliverables to a read-back-verified PayPal Sandbox draft.**

Status: executable Python integration core, locally tested. **Not a completed hackathon application.** No authenticated PayPal or AI call has been completed in the originating environment. The UI, client authentication, full AI evaluation, public repository and submission video are not complete.

## What exists

- The original scope/evidence guard, with explicit SQLite connection cleanup.
- Server-side PayPal Sandbox OAuth, invoice creation, and direct GET verification. No live endpoint, invoice send, payment capture, refund or mark-paid method.
- A durable SQLite intent ledger, committed before the invoice POST. A crash, lost reply or ambiguous response does **not** permit automatic creation again.
- Read-only reconciliation using the previously saved invoice ID, or a candidate ID obtained from the sandbox dashboard. The invoice's number, sender, recipient, currency, lines, quantity, unit value, total and DRAFT status must match.
- A locally signed approval bound to the complete draft. This is a local-process capability, **not an authenticated customer portal** and not evidence of customer consent.
- A Responses API adapter with a strict JSON schema and exact evidence quotations. No prices, approval tools or payment capabilities are supplied to the model. Real inference is not yet validated. An exact quote is **not** proof of relevance, truth or acceptance.
- A five-scenario fault demonstration using actual loopback HTTP and an explicitly simulated PayPal service. It tests our application logic, **not PayPal's behavior or idempotency guarantees**.

## Run without accounts or network

Requirements: Python 3.11+; the standard library only. Put all the Python files in the same folder.

```sh
python reproduce.py
```

This runs the 98 local tests and the five-scenario HTTP mock. It does not call a model, notify a customer or create a PayPal invoice. `INV2-MOCK-0001` is a fixture ID, never a real provider receipt.

## Check external readiness

```sh
python run_scopeproof.py preflight --probe-network
```

The command prints configuration booleans, not credentials. DNS resolution alone does not demonstrate authentication or a working invoice integration. The original session had no credentials configured and could not resolve PayPal/OpenAI domains. A PayPal connector was searched for; the surfaced plugin could not be enabled in that workspace.

## Sandbox draft smoke test — intentional external write

Use an actual sandbox merchant application with invoicing enabled and a sandbox buyer. Never use real customer documents or a live account. Configure these variables through the operating system or deployment secret manager:

- `PAYPAL_SANDBOX_CLIENT_ID`
- `PAYPAL_SANDBOX_CLIENT_SECRET`
- `PAYPAL_SANDBOX_SELLER_EMAIL`
- `PAYPAL_SANDBOX_BUYER_EMAIL`

Do not paste secrets into chat, source code, public repositories, screenshots or command-line arguments. `.env.example` is documentation only and is not automatically loaded.

When deliberately invoked with the flag below, the smoke test locally approves **synthetic demonstration evidence** and attempts to create one **125.00 EUR sandbox DRAFT**. It is not a real customer's approval or a request for payment. Local state is stored in `.scopeproof-private/`.

```sh
python run_scopeproof.py sandbox-draft --confirm-sandbox-draft
```

The same workspace and project/milestone key protect against repeating a POST after an uncertain result. **Do not delete the ledger or rerun under a new workspace to bypass an UNKNOWN state.** Local signing keys remain private. On Windows, review the private folder's ACLs: POSIX chmod is not a Windows ACL guarantee.

A verified draft is never labelled paid or sent by this software. Repeating the command re-reads an already verified invoice: a failed refresh is not presented as fresh verification.

### Lost response

If the creation response is lost, the ledger remains `UNKNOWN` or `IN_FLIGHT`. Obtain the candidate invoice ID from the PayPal Sandbox dashboard if one was not saved, then run:

```sh
python run_scopeproof.py reconcile --billing-key BILLING_KEY --invoice-id INV2-VALID-SANDBOX-ID
```

This command only reads an invoice and validates it against the stored intent. A missing or different invoice does not trigger creation again. There is deliberately no blind retry based on an assumed `PayPal-Request-Id` retention policy: PayPal says support/retention are API-specific, and this integration has not verified the provider's behavior.

## Optional real AI smoke test — may incur provider fees

The default is **off**. Configure `OPENAI_API_KEY` and `SCOPEPROOF_AI_MODEL`, choosing a model that supports the Responses API and the schema. The model name is deliberately not guessed. Then authorize a single metered call explicitly:

```sh
python run_scopeproof.py ai-check --allow-metered-ai-call
```

This sends only a small synthetic example. It cannot approve an invoice, change money or create a payment. The request uses `store:false`; that is not a general claim that the provider keeps no logs or that the system meets any particular privacy law. Provider pricing must be checked before enabling. No additional spending was authorized or incurred in the original session.

## Security boundary and limitations

The local filesystem and calling process are trusted. The HMAC key holder can approve local actions; this does not identify a client. Production use requires authenticated roles, CSRF/session protection, tenant isolation, durable storage and operational recovery. The local event hash chain detects an accidental edit; a privileged person can recompute it or delete it. It is not independent notarization.

Amounts are rebuilt from the current scope; the remote payload is not accepted directly from model output. Complete evidence does not automatically imply a deliverable is good. A person must review the content, not merely click because the model returned a quote. There is no quality measurement from a real LLM yet.

Concurrent requests are covered only within this controlled application using one shared ledger. PayPal's own concurrency, webhook delivery and idempotency are not certified by a mock. `REVIEW_REQUIRED` has no automatic escape hatch. No endpoint for payments or automatic sending is implemented.

## Official references, checked 15 October 2026

- Rules, rubric, eligible deliverables: https://paypalaihackathon.devpost.com/rules
- Sandbox invoicing setup: https://developer.paypal.com/api/invoicing/
- Create invoice schema: https://developer.paypal.com/api/invoicing/v2/invoices-create
- PayPal idempotency scope: https://developer.paypal.com/api/rest/reference/idempotency/
- Responses schema output: https://developers.openai.com/api/docs/guides/structured-outputs

No relationship with, endorsement by or prize from PayPal is asserted. The development and checks were performed using ChatGPT for Carlosjv. Local tests are not an independent audit and do not imply a probability of winning.
