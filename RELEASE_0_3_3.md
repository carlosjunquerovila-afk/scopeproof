# ScopeProof 0.3.3 — edit safety and a fresh AI demonstration

Released candidate prepared 16 October 2026. The application remains a local prototype; the default invoice provider is a simulator.

## Product fix

Evidence and scope edits now remain visible until explicitly saved or discarded. Reviewing, importing analysis, exporting, refreshing and preparing a draft require the saved version. Initial editors stay disabled until state arrives. API actions are serialized while typing remains possible, preventing an older response from replacing a newer saved state. Edits made while a request is pending are preserved.

The scope includes name, amount, currency and acceptance criteria. Both editors can be saved sequentially without dropping the other's draft. This does not make the browser session a durable document editor: an intentional reload after accepting the browser's unsaved-changes warning can still discard pending edits.

## Evidence

- 192 internal Python tests pass, with five inherited simulator HTTP fault scenarios.
- 19 controller checks pass against the actual JavaScript with DOM/HTTP adapters and a real Python workspace initial state. They are not browser-rendering or browser-to-server tests.
- Two newly generated external ChatGPT responses were imported over actual loopback HTTP in a synthetic incomplete-to-complete case. The original run was on 0.3.2; saved-output replay is separately recorded for 0.3.3. The app made no model API request.
- The HTTP case checks no automatic approval, one simulated draft across a retry, approval revocation after edits, and rejection of old model output/reviewer links.

## Still pending

Actual authenticated PayPal Sandbox create/read-back; public source publication; final recorded demo and YouTube publication; final eligibility/project-origin declarations and Devpost submission. No production readiness, customer identity, customer demand, real payment or prize is claimed.
