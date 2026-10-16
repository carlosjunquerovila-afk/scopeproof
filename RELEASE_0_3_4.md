# ScopeProof 0.3.4 — publication candidate

Prepared and locally verified 16 October 2026. `VERIFICATION_0_3_4.txt` records **202 Python tests, five local HTTP fault scenarios, 21 JavaScript-controller checks and 16 historical-replay HTTP requests**, all passing. It includes the verified runtime hashes. All provider responses were simulated; no new model inference, actual PayPal API call, payment or customer trial occurred in this verification.

## Publication changes

- The repository is self-contained for local use: Python 3.11 or later and `python app.py` from its root are sufficient. The README no longer depends on a separately distributed installer.
- The README gives an explicit source-based saved-response replay command that leaves original evidence unchanged.
- English and Spanish onboarding distinguish earlier test evidence from this candidate's pending final results and separate Sandbox authentication from draft creation and read-back.
- A publication `.gitignore` excludes credentials, private application state, database files, local outputs and generated Python caches. Files still require inspection before publication.

## Backend changes confirmed by the implementation reviewer

- New workspaces use a distinct persisted identity. Reopening a workspace retains it; existing workspaces retain their earlier identity.
- Sandbox creation sends a stable `PayPal-Request-Id` derived from the persisted payload. No automatic POST retry was introduced, and provider-side idempotency has not been verified against the real API.
- HTTP 400, 401, 403, 404, 405, 406, 415 and 422 create responses produce `CREATE_REJECTED`, retaining only a `PAYPAL_DRAFT_HTTP_N` reason and keeping the operation blocked for review. HTTP 408, 409, 429, server errors and network failures remain `UNKNOWN`.
- The CLI uses a per-workspace identity, preserves legacy identity and refuses to proceed when a signing key is missing beside an existing ledger.

The initial focused backend review covered 140 tests across bridge, workflow, runner and recovery, including ten new regressions. The final integrated run passes all 202 Python tests. These are local tests with controlled provider responses; no successful real Sandbox run is claimed.

## Interface and presentation changes

- Review cards display each criterion, analysis status and reason, supporting quotation and human decision together. The analysis summary is separate from acceptance; imported model output does not approve anything automatically.
- `CREATE_REJECTED` blocks another creation and hides reconciliation. Only an allowlisted HTTP reason is shown, without exposing a raw provider response.
- The local demo script and narration now lead with the version-specific acceptance problem, show the evidence-to-decision workflow, and explicitly retain real Sandbox integration as pending.

The interface reviewer reports a passing JavaScript syntax check and 21 passing controller checks: 19 inherited checks plus two new cases for criterion/quote/decision pairing without auto-acceptance and explicit rejection without another POST or raw error display. The checks use DOM/HTTP adapters; they do not establish browser rendering, video footage or provider integration.

## Evidence preserved with its original scope

- Version 0.3.3 recorded 192 internal Python tests, five inherited simulator HTTP scenarios and 19 JavaScript-controller checks. These reports remain historical evidence.
- The original fresh external ChatGPT demonstration ran on `0.3.2-evidence-limits`; it imported two newly generated responses across 16 actual local HTTP requests.
- Its saved outputs were replayed on `0.3.3-edit-safety`. That replay involved no new inference.
- The 0.3.4 replay also passes 16 actual HTTP requests. The harness reconstructs the historical `demo-web-project` identity only in a temporary simulator workspace, preserving exact archived prompt fingerprints and model responses. Normal runtime identities are unaffected. Fifteen historical evidence files were verified unchanged.
- Those demonstrations used synthetic work, a simulated reviewer and a simulated invoice provider. They made no application-to-model API call or actual PayPal API call.

## Release gates still open

- Authenticated PayPal Sandbox draft creation and matching direct read-back from the application.
- Public source publication and an English video under three minutes showing the final product and the actual demonstrated AI interaction.
- Final Devpost declarations, submission and confirmation receipt.
- Independent user feedback and commercial validation. The €99 supervised-pilot price remains an untested hypothesis.

No payment, sale, customer outcome, production certification or competition result is claimed.
