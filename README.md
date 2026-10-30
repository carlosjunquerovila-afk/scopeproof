# ScopeProof 0.3.5 — delivery workflow candidate

**Evidence before invoices.** ScopeProof helps a web studio connect agreed scope, delivery evidence, explicit version-specific review and an invoice draft. AI assists the review; a person decides whether to accept the work. The price comes from the agreed scope.

## Current entry and demonstration

**Status reconciled on 30 October 2026:** the existing [Devpost entry](https://devpost.com/software/scopeproof-h4bvsr) was submitted on 23 October and its completed **5/5** submission was last inspected on 26 October. The public [143-second demonstration of 0.3.5](https://www.youtube.com/watch?v=43xjJ_O0N00) is the current judging video. These dated records supersede the earlier draft/pending-publication statements in the historical sections below; they are not a new submission or a prize result.

The video demonstrates the local simulator workflow with disclosed imported external AI analysis. It uses sampled consecutive captures with cuts and reading holds; it is not a continuous native screen recording. It must not be presented as one continuous browser-to-AI-to-PayPal execution. The real PayPal Sandbox core-adapter receipt remains the separate historical run linked below. For the shortest reproducible judging path, use [the current judging guide](submission/CURRENT_JUDGING_GUIDE.md).

## New in 0.3.5: a usable delivery handover

The existing local application now downloads a self-contained delivery record from the saved workspace: agreed scope and price, criterion findings and quotations, explicit review, evidence and draft status. It opens offline and includes print styles. The record marks expired acceptance and distinguishes an earlier draft from the current evidence. Exporting does not create, send or pay an invoice. The new **Download delivery report** button is blocked while scope or report edits are unsaved.

The recorded local 0.3.5 checks passed **214 Python tests, five HTTP fault scenarios and 24 JavaScript-controller checks**. A new synthetic project completed **16 actual loopback HTTP requests**, downloading records before acceptance, after an explicitly accepted version and after a later edit revoked acceptance. The provider and reviewer were simulated; no browser rendering, model inference or PayPal request is claimed for this new run.

The candidate uses runtime `0.3.5-delivery-record`. See [the workflow and verification guide](DELIVERY_WORKFLOW_0_3_5.md) for the user flow, offline integrity checker and fresh-project HTTP reproduction. The changes extend the local product; no hosted service, customer authentication, browser-to-PayPal demonstration or commercial validation is added.

## Historical 0.3.4 verification baseline

**Recorded status, 19 October 2026, before this delivery change:** version 0.3.4 passed its recorded local verification: **202 Python tests, five HTTP fault scenarios, 21 JavaScript-controller checks and a 16-request historical-response replay**. A separate one-shot GitHub Actions run authenticated to PayPal Sandbox, created an unsent synthetic draft through the core adapter and verified a direct read-back. The default UI still uses a clearly labelled provider simulator; browser-to-server-to-PayPal execution has not been demonstrated. Devpost registration is complete and the entry is saved as a draft, not finally submitted.

The recorded results below belong to the indicated runtimes. `VERIFICATION_0_3_4.txt` records the local 0.3.4 checks and verified runtime file hashes; the later Sandbox run is recorded separately below. Earlier reports remain historical evidence. See `RELEASE_0_3_4.md` for the changes.

| Verification | Recorded result | Boundary |
|---|---|---|
| Python application tests, 0.3.4 | 202 passing tests | Internal policy, workflow, recovery and HTTP checks with simulated providers; includes ten new backend regressions. |
| HTTP fault demonstration, 0.3.4 | Five scenarios pass | Local failure handling, reported separately from the Python test count. |
| Interface controller checks, 0.3.4 | 21 passing checks; JavaScript syntax check passes | Real application JavaScript with DOM/HTTP adapters. Includes criterion-to-quote matching without automatic approval and rejection without another creation request. No browser rendering or provider validation. |
| Fresh external AI review through real app HTTP | Two newly generated ChatGPT responses imported and validated; 16 requests; all recorded checks pass | Original fresh run used runtime `0.3.2-evidence-limits`. A 16-request saved-output replay also passed on `0.3.3-edit-safety`. The app made no model API calls; provider responses were simulated. |
| Historical-response replay, 0.3.4 | 16 actual loopback HTTP requests pass in `demo_evidence/replay_0_3_4.json` | The harness reconstructs the legacy project identity only inside a temporary simulator workspace. Original prompt and response bytes are unchanged. No new inference or PayPal call. |
| PayPal Sandbox core-adapter create + direct read-back | `VERIFIED_DRAFT` in [one-shot run #1](https://github.com/carlosjunquerovila-afk/scopeproof/actions/runs/39273764876); [redacted receipt](demo_evidence/sandbox_transport_20261019.json) | Exact 0.3.4 adapter on a GitHub Actions runner, with synthetic local review. OAuth, draft POST and matching GET were verified. No app UI, fresh inference, customer approval, send or payment in this run. |

These are internal checks, not an independent audit, production certification, customer study or prediction of a prize.

## Start in one command

Use a desktop with Python 3.11 or later. Clone or download [the repository](https://github.com/carlosjunquerovila-afk/scopeproof), open a terminal in its root folder and run the command below. The source checkout is sufficient: no separate installer, package download or model download is required. The application, local simulator and Python tests use only the Python standard library.

```sh
python app.py
```

The app binds only to `127.0.0.1` and opens a private local merchant session. State is stored under `~/.scopeproof-local/`. Ctrl+C stops the process; no background service is installed. Run one process per workspace. For an isolated demonstration:

```sh
python app.py --workspace ./scopeproof-demo
```

Do not share merchant/reviewer session links or record their tokens. Do not delete a ledger to bypass an uncertain provider outcome. Demo and Sandbox ledgers are separate.

The default banner is **LOCAL SIMULATOR · NOT PAYPAL**. Identifiers beginning `INV2-MOCK-` are simulated records, not PayPal receipts. Supplied reports describe synthetic work.

## Why this workflow

A studio's agreement, delivery report, acceptance and invoice preparation can refer to different versions as a project changes. ScopeProof brings them into one reviewable sequence: which criteria were considered, what text supported them, which version was accepted and which draft was prepared from that acceptance.

The first intended users are small web studios delivering fixed-price website milestones. Faster review and fewer avoidable corrections are hypotheses to measure; no customer savings or demand is established by this prototype.

## Walk through the application

1. Read the agreed milestone, fixed integer-cent price, currency and acceptance criteria.
2. Inspect the incomplete sample report. Locate candidate passages locally, or import a review produced by an AI tool.
3. Choose **Use complete sample**, then **Save new version**. Unsaved report edits are marked. Actions that use or reload the saved report are blocked until you save or explicitly discard those edits.
4. Open a separate review session. Inspect each criterion and the underlying work; explicitly accept each criterion and the current version.
5. Return to the merchant session, refresh and separately confirm draft creation.
6. Inspect the result and export the local record. A changed evidence version invalidates the previous acceptance.

The 0.3.4 review cards put each criterion, the analysis status and reason, its quoted evidence and the human decision together. The analysis summary is displayed separately from acceptance: importing a model response does not check approval boxes or approve the milestone.

One textual milestone per workspace is supported. The program does not independently inspect a deployed website or verify that a report is true. A person can make a wrong acceptance decision; AI findings do not replace that person's review.

### Demonstrate recovery without a second creation

In the simulator's fault laboratory, select **Persist draft, then lose the response** before the first draft attempt. After explicit review and draft confirmation, the result becomes `UNKNOWN`. Repeating the action does not make a new blind creation request. Choose **Reconcile by reading, never recreate** to inspect the existing simulated record. A matching read can establish `Simulated draft verified`.

This fault is deliberately injected locally, not an observed PayPal outage. An uncertain real provider outcome remains unresolved if no matching candidate invoice can be found. A failed lookup does not prove that creation failed.

## AI assistance and its boundary

Select **Import review from your AI tool**. Export the prompt for the current snapshot, obtain a response from the chosen tool and paste the JSON back into ScopeProof. The backend checks the snapshot fingerprint, closed schema, criterion identifiers and exact quotations. It labels the response as imported and its author as unverified.

The prompt intentionally omits invoice amounts and seller/buyer email fields. User-entered evidence can still contain sensitive information; review it before sending it to an external model.

`examples/incomplete_review.json` and `examples/complete_review.json` are saved ChatGPT-assisted analysis for historical snapshots. New 0.3.4 workspaces have distinct identities, so those responses are not interchangeable with a fresh workspace's current prompt. Use the replay harness below to reproduce the historical fixture, or obtain a new response for the prompt exported by the current workspace. Importing a saved response is a replay, not fresh inference. A mismatching response is correctly rejected as stale.

### Fresh execution evidence

A separate recorded demonstration exported two prompts through the actual loopback HTTP server and imported two freshly generated external ChatGPT responses. In the incomplete case, the model found paraphrased responsive-layout support and marked the untested contact form and outstanding accessibility assessment missing despite an embedded instruction to mark everything passed. Corrected evidence received a new external response with support for all three criteria.

The import did not approve the milestone. A simulated local operator explicitly approved the exact version; draft creation and retry left one simulated invoice. A later edit revoked acceptance, rejected the old analysis and invalidated the old review link. The original run is documented in `demo_evidence/fresh_run.json`, with timestamps and prompt/response hashes. It used runtime `0.3.2-evidence-limits`; the saved-output replay passed on `0.3.3-edit-safety` and is recorded separately. The replay made no new model inference.

The 0.3.4 harness also passed those 16 HTTP requests using a temporary simulator fixture with the original `demo-web-project` identity. Its receipt is `demo_evidence/replay_0_3_4.json`; normal runtime identity generation is unchanged. The retained `demo_evidence/README.md` and `manifest.json` describe the earlier evidence package, including the earlier harness hash. `MANIFEST_0_3_4.json` records the current evidence-directory files without relabelling the original generation.

This establishes **fresh external model analysis plus real HTTP import**, not an in-app model API call. The application cannot authenticate the pasted response's author. The evidence and review actor were synthetic/simulated; no customer participated. Literal quotations can still mislead, and these two examples do not establish general model accuracy. No footage of this run is claimed.

Other available paths:

- **Local text search:** TF-IDF passage retrieval, explicitly labelled as not an LLM; no positive semantic acceptance decisions.
- **Installed local LLM / Ollama:** optional adapter for an already installed loopback model. No model is installed or downloaded by the app; cloud offload must be disabled. No successful Ollama run is claimed here.
- **Guarded OpenAI core adapter:** available in `run_scopeproof.py`, requiring configured credentials/model and its metered-call execution flag. Adapter code is not proof of a successful model call.

No model path can approve the milestone, set the agreed price or execute a payment.

## Connect PayPal Sandbox privately

```sh
python app.py --sandbox --workspace ./scopeproof-sandbox
```

Use the private connection panel on the computer running the app. Authenticate through the official PayPal Developer dashboard and use authorized Sandbox credentials and test accounts. Enter the Sandbox Client ID and secret locally, never in a public repository, video or chat.

The supported seller domain is `@business.example.com`; the buyer domain is `@personal.example.com`. Custom test email domains are not supported. Authentication and draft creation are separate actions; connecting alone does not create an invoice.

Credentials remain in the running server process and are not written by the app to its workspace database, exported report, source or application logs. Browser credential fields are cleared after the attempt. The local process, operating system and filesystem remain trusted; memory, privileged debugging and system crash dumps are outside that assurance. Re-enter credentials after restarting.

The core adapter has a recorded authorized Sandbox draft creation and direct read-back matching supported fields, captured in `demo_evidence/sandbox_transport_20261019.json`. That one-shot runner did not exercise the browser workflow below. Browser login, OAuth success alone or a simulator receipt would not establish this provider result.

### Sandbox run checklist

1. Use an authorized PayPal Developer account, its **Sandbox** application credentials and test seller/buyer accounts. Confirm that the computer running ScopeProof can reach the PayPal Sandbox API.
2. Start the command above in a new Sandbox workspace. Keep that workspace for the entire run and any recovery; do not reuse a simulator ledger as provider evidence.
3. Enter the Sandbox credentials privately in the connection panel and authenticate. Recheck the environment label and seller/buyer test addresses before proceeding.
4. Save the agreed scope and delivery report, generate or import a review for that exact version, and explicitly approve the criteria and current version in the review session.
5. Return to the merchant session and confirm draft creation once. Check the direct read-back against the agreed amount, currency, parties, description and invoice number. If the outcome is uncertain, reconcile by reading the existing draft; do not reset the workspace or blindly recreate it.
6. Keep the private run record locally. Any public evidence must omit credentials and session capabilities and clearly identify Sandbox. Stop the server with Ctrl+C. A successful draft remains unsent and unpaid.

The app has no production host, invoice-send, capture, refund or mark-paid action. A draft is not sent, paid or revenue. Lost-response Sandbox reconciliation needs a candidate invoice ID from the authorized test account.

### Draft identity and provider outcomes in 0.3.4

New workspaces receive distinct, persisted identities; reopening a workspace keeps its identity and existing workspaces retain their earlier one. The PayPal adapter derives a stable `PayPal-Request-Id` from the persisted draft payload. These are local implementation properties: provider-side idempotency has not been demonstrated against PayPal.

An explicit supported HTTP rejection is recorded as `CREATE_REJECTED` with only a status-derived reason; raw provider error bodies are not exposed in that reason. Ambiguous responses, rate limits, server failures and network errors remain `UNKNOWN`. Both paths retain the operation for investigation; neither triggers an automatic creation retry. Review the existing record before taking any further action, and keep the workspace and ledger intact.

## Reproduce the checks

```sh
python run_tests.py
```

For the JavaScript controller checks, use an installed Node.js runtime:

```sh
node test_ui_unsaved.js
node --check static/app.js
```

Controller tests exercise the real `static/app.js` with DOM/HTTP adapters and initial state from the Python workspace. They cover unsaved-report status, actions blocked against stale saved text, explicit discard, failed saves and delayed responses. They do not establish visual rendering, actual navigation-dialog behavior or browser-to-server-to-PayPal execution.

The 0.3.3 correction protects unsaved report and scope edits, including name, amount, currency and criteria. API actions are serialized and late responses preserve newer typing. It does not implement autosave or claim equivalent protection for imported JSON. A deliberate reload after accepting the browser warning can still discard unsaved edits. `UX_AUDIT_20261016.md` describes the finding. Earlier release documents retain historical results; their counts do not describe this candidate.

## Trust and integrity boundaries

Private per-run capabilities, exact Host/Origin checks, JSON-only writes, a CSRF header, method/field allowlists, state revisions and durable draft intents are implemented. These controls do not establish production security.

- A review link proves possession of a temporary local capability, not customer identity, KYC, a legal signature or organizational separation of duties. The local operator can obtain both merchant and reviewer links.
- Local hashes and a signing key bind workflow records but are not independent notarization. A privileged local owner remains trusted.
- Preventing blind retries is this application's policy, not a provider-wide exactly-once guarantee or a promise of automatic recovery.
- Direct read-back verifies supported fields at that read, not their future state. Restored records remain historical until a new explicit provider read.

## Commercial test, not claimed traction

The current proposed experiment is ten qualified studio prospects, three supervised usability sessions and two paid pilot offers at **€99 per pilot**, covering one project and up to three guided milestone reviews. This €99 hypothesis supersedes an earlier €49 planning figure; neither price has been validated.

Measure actual review time, corrections, misunderstandings, delivery labor and operating cost. Keep production invoicing in the studio's existing system during a supervised service pilot. No outreach, sale, paid pilot, realized savings or revenue is claimed here.

## Final-entry gates

- [x] Local application, explicit review, version binding and recovery workflow.
- [x] Earlier Python and JavaScript-controller results documented separately, with their runtime versions.
- [x] Fresh external AI responses imported over real local HTTP; exact boundary documented.
- [x] Existing Devpost entry submitted on 23 October; completed 5/5 form last inspected on 26 October: https://devpost.com/software/scopeproof-h4bvsr
- [x] Replay the saved AI outputs over 16 actual HTTP requests on `0.3.3-edit-safety`; no fresh model inference during replay.
- [x] Local integrated verification of the final 0.3.4 runtime recorded in `VERIFICATION_0_3_4.txt`.
- [x] Actual core-adapter-to-PayPal Sandbox draft creation and matching direct read-back in the one-shot runner; synthetic local review only.
- [ ] Browser-to-server-to-PayPal workflow with fresh AI interaction and explicit UI review.
- [x] Public MIT source for 0.3.5 and the current 143-second video linked above; simulator, imported analysis and historical Sandbox boundaries remain explicit.
- [x] Existing submission and confirmation receipt recorded; this does not independently certify every personal eligibility or origin declaration.
- [ ] Independent user evidence and commercial validation.

The closing time recorded in the latest campaign review is 12 November 2026 at 12:00 PST / 21:00 Europe/Madrid. Recheck https://paypalaihackathon.devpost.com/rules before a future material change. The existing submitted entry must not be duplicated; submission, eligibility and winning are separate states.

## License and attribution

MIT License; copyright Carlosjv. The implementation, saved analysis examples, documentation and internal reviews were authored with ChatGPT. No independently audited product, guaranteed win or real payment is claimed.

Official references: https://developer.paypal.com/api/invoicing · https://developer.paypal.com/api/get-started/ · https://docs.ollama.com/api/chat · https://developers.openai.com/api/docs/guides/structured-outputs

## Replay the saved AI evidence from source

From the repository root:

```sh
python demo_evidence/run_demo.py --app . --replay --output ../scopeproof-local-replay.json
```

This starts a temporary local simulator workspace, explicitly reconstructs the historical project identity and imports the saved responses over real loopback HTTP. It performs no new inference and no PayPal call. The new result is written outside the source tree; the original evidence files remain unchanged. A successful run establishes a saved-output replay on the runtime named in that new result, not a new external AI generation. The legacy fixture is confined to the replay harness and is never applied to a Sandbox workspace.

## Publishing the source

Publish source, static assets, tests, documentation and the intentionally recorded synthetic evidence. Keep `LICENSE` and the evidence provenance with them. The provided `.gitignore` excludes credentials, private workspaces, databases, keys and local runtime output. It is a convenience, not a secret scanner: inspect the files being committed and never publish private session links, Sandbox credentials or unsanitized exports. `.env.example` contains empty documentation fields and is not automatically loaded by the app.
