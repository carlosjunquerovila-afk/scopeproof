# Observed browser workflow with PayPal Sandbox — 9 November 2026

ScopeProof completed an observed browser-driven workflow using **fresh external ChatGPT reviews imported as JSON**, a separate reviewer test session, real PayPal Sandbox authentication, one unsent EUR 125 draft and a matching read-back. A later evidence edit revoked acceptance; **Read existing draft only** successfully reread the same draft without accepting the new version.

This extends the earlier evidence. It does **not** establish embedded model inference, independent customer acceptance, production readiness, provider-wide exactly-once behavior or a new demonstration video. The assistant operated both local roles under the owner's authorization, using synthetic evidence. The application still labels imported authorship as unverified.

## Evidence and source

- [Sanitized observation receipt, prompts and fresh responses](../demo_evidence/sandbox_browser_20261109.json).
- Runtime source: `8b176a695cf9516aa0093425b45bfee01c685917`, reporting `0.3.5-readback-candidate`.
- The supplied launcher embeds ten runtime files whose hashes match that build. The browser was on the user's Windows computer; the running process was not independently attested.
- Observation method: connected Chrome controls, visible application states and its rendered event history. The receipt is an assistant's observation, not an independent provider certificate.
- The additional PayPal Developer API-log inspection was blocked after a sign-in redirect. No raw provider response or dashboard-log export is included.

## What happened

All times below are **Europe/Madrid, 9 November 2026**, as displayed in the application history.

| Time | Observation |
| --- | --- |
| 17:21:32 | Fresh review of incomplete v1 imported: three missing criteria. |
| 17:22:06–17:23:23 | Complete v2 saved; the old JSON was rejected with `AI_REVIEW_STALE`; a fresh review was imported; explicit acknowledgement and every criterion were required before test-role acceptance. |
| 17:26:49 | Saving v3 revoked acceptance. The old reviewer session returned `REVIEW_SNAPSHOT_CHANGED`. |
| 17:33:06 | Real Sandbox OAuth succeeded. Updating the test parties produced v4 and cleared prior review/acceptance. Connecting created no invoice. |
| 17:34:03–17:34:34 | A fresh response for the v4 prompt was imported and the separate reviewer test session accepted that exact version. |
| 17:35:20 | The merchant's create control was activated once. The application reported `VERIFIED_DRAFT` after matching the agreed amount, recipient and line. |
| 17:36:22 | Saving v5 revoked acceptance and labelled the draft as belonging to the earlier version. |
| 17:36:33 | The explicit read-only control reread the same invoice identifier. The current version remained unaccepted. |

Accepted v4 fingerprint: `8efcf3bed4fb5c66be5670b0da71c6cd9db4c12671ffd398b5496d4339dc920b`.

Unaccepted v5 fingerprint: `6ed9ba37492f02c8683a787aee0e7220255849fe09b127cab86a86e8b1b2d8c3`.

The invoice identifier is withheld; its SHA-256 is `21569dc291b945ba6adcf0f1ad6ddc8c376cad626cc3d9c58ce04b928cf680e6`. No credential or private session capability is included. Automatic browser translation altered some displayed event names; the receipt preserves the visible text, and the table above describes their meaning.

## Reproduce the supported path

1. Follow the [private Sandbox setup](../README.md#connect-paypal-sandbox-privately) on the same computer as the browser, using your own Sandbox application and test accounts. Keep the console running.
2. Authenticate first: changing the parties clears the previous review and acceptance.
3. Export the current review prompt, obtain a **new** response from an external AI tool and import it. A saved response only demonstrates replay; it does not demonstrate fresh inference.
4. Open the separate reviewer session, inspect the evidence and explicitly accept the criteria and version. Disclose when this is a test role rather than a real customer.
5. Confirm one unsent Sandbox draft. If the outcome is uncertain, preserve the workspace and investigate/read the existing intent; never delete the ledger or create a replacement to force a success.
6. Save an evidence edit and confirm that current acceptance is revoked. Use **Read existing draft only** to verify the original draft without creating another one.

The delivered-site assertions are synthetic text, not measurements of a real website. Three illustrative model responses are not a model-quality benchmark. The 143-second public video remains the earlier simulator demonstration; this run was not recorded as a continuous video.

The delivery-report control returned its success notice, but the downloaded file's bytes were not inspected in this browser run. A JSON-download observer timed out; that export is not counted as verified. Existing automated export tests retain their separate scope.
