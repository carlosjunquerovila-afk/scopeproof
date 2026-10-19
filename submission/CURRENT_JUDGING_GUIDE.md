# ScopeProof — judge quick start and evidence boundaries

ScopeProof is a local desktop-browser prototype for a web studio's fixed-price milestone: agreed criteria, textual delivery evidence, AI-assisted findings, an explicit version-specific review, and an invoice draft. It is MIT licensed and uses Python 3.11+ standard library, SQLite and HTML/CSS/JavaScript. The [public source repository](https://github.com/carlosjunquerovila-afk/scopeproof) contains the application and full README.

## Run the working build

On the **same computer as the browser**, open a terminal in the extracted repository root and run `python app.py` (Windows PowerShell: `py -3.11 app.py`). The app binds to `127.0.0.1:8765`, opens a private local session and needs no dependency installation or credentials in its default mode. Leave the terminal running; use the complete private URL printed there if a browser did not open. Do not share that session URL. The banner says **LOCAL SIMULATOR · NOT PAYPAL**. The README gives the review walkthrough. A remote container's `localhost` is not your computer's browser. For Windows, an alternative is the portable launcher from the public [v0.3.4 release](https://github.com/carlosjunquerovila-afk/scopeproof/releases/tag/v0.3.4): run `py -3 ScopeProof_ejecutar_0_3_4.py` with Python 3.11 or newer. Default mode does not contact PayPal. Stop with Ctrl+C.

The AI interface exports a prompt tied to the current snapshot; a response obtained from an external AI tool is imported and checked for schema, criterion IDs, exact quotations and version. The app cannot authenticate the pasted response's author or independently establish that reported work occurred. A model finding never approves the milestone; the separate local reviewer action does. Its capability link does not prove a customer's identity.

## What the evidence establishes

| Evidence | Observed result | Boundary |
| --- | --- | --- |
| Fresh AI import, 19 Oct 2026, 0.3.4 | Two newly generated ChatGPT analyses from two app-exported prompts imported through 16 real loopback HTTP requests; synthetic incomplete report left two criteria missing, corrected report supported all three. | Same-assistant synthetic evaluation, model ID not asserted, no in-app model API, no browser footage, local simulator invoice/reviewer, no PayPal call. The sanitized trace is preserved locally pending public packaging. |
| PayPal Sandbox, 19 Oct 2026 | [One-shot runner](https://github.com/carlosjunquerovila-afk/scopeproof/actions/runs/39273764876) and [redacted receipt](https://github.com/carlosjunquerovila-afk/scopeproof/blob/main/demo_evidence/sandbox_transport_20261019.json): OAuth, an unsent synthetic EUR 125 draft and direct matching GET (`VERIFIED_DRAFT`). | Exact 0.3.4 core adapter on GitHub Actions with synthetic local review; no ordinary-browser UI, new AI inference, customer approval, send or payment in this run. Do not redispatch. |
| Internal 0.3.4 checks | 202 Python tests, five injected HTTP fault scenarios, 21 JS-controller checks and a 16-request saved-output replay passed in the recorded verification. | Controlled providers and DOM/HTTP adapters; the replay is not fresh inference. No independent certification. |

The AI and real PayPal results are **two separate executions**, not one continuous browser-to-PayPal transaction. The default UI simulator allows direct testing without private credentials; optional Sandbox mode requires a judge's own free PayPal Developer Sandbox app and generated test accounts per the main README. Credentials and private identifiers are not distributed.

The [Devpost narrative](https://devpost.com/software/scopeproof-h4bvsr) describes these boundaries. A planned 173-second production script is not recorded footage. A public YouTube video under three minutes, its Devpost link, personal eligibility/ownership declarations, and final submitted receipt remain to be completed. No customer study, paid pilot, real payment or prize is claimed.
