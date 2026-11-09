# ScopeProof — judge quick start and evidence boundaries

**Maintenance build and observed run, 9 November 2026.** The [existing Devpost entry](https://devpost.com/software/scopeproof-h4bvsr) was inspected on 9 November as **Submitted, 5/5 steps complete**, with the [143-second video](https://www.youtube.com/watch?v=43xjJ_O0N00). No duplicate entry was created. This build is not the code shown in that video.

ScopeProof is a local desktop-browser prototype for small web studios: fixed scope, textual evidence, AI-assisted findings, version-specific review and an unsent draft. It does not independently test a delivered website.

## Start the working application

Use Python 3.11+ on the **same computer as the browser**. In the source directory:

```sh
python app.py --workspace ../scopeproof-judge-demo
```

Windows Python launcher: `py -3 app.py --workspace ../scopeproof-judge-demo`.
Use the private URL printed by the application if the browser does not open. Do not record its token. The banner is **LOCAL SIMULATOR · NOT PAYPAL**. No credentials, dependencies or model download are needed in default mode.

1. Load the complete synthetic sample and save it.
2. For AI import, choose **Import review from your AI tool**, export the prompt for this snapshot, obtain a fresh response from your own tool and validate its JSON. Importing is not in-app inference or authenticated authorship.
3. Open the separate review session; inspect and accept each criterion and the saved version. Review links do not prove customer identity.
4. Return to the merchant tab, **Refresh local status**, then explicitly confirm the simulated draft.
5. Download and open the delivery report. Save an evidence change: acceptance must be revoked and the old draft must remain attached to its original version.
6. In this candidate, **Read existing draft only** refreshes that original draft without new acceptance or creation. Failed reads are not fresh verification; mismatches require investigation.

## One-command local verification

An installed Node.js is needed for JavaScript checks, but not for application use:

```sh
python tools/verify_judging.py --output ../scopeproof-judge-check-01
```

Use a new output directory outside the source tree. The command records source hashes, logs, actual counts, two separate 16-request HTTP flows and readable delivery files. Missing Node or a failed check yields `FAILED_OR_INCOMPLETE`.

The 9 November candidate passed **236 Python tests, five HTTP fault scenarios, 27 JavaScript controller checks**, syntax validation and both HTTP flows. The controller uses DOM/HTTP adapters, not browser rendering. One flow replays frozen external responses; the other uses local lexical retrieval. Neither is fresh inference or PayPal execution. Attribute results to the source hashes in the receipt.

## Evidence map

| Evidence | Establishes | Boundary |
| --- | --- | --- |
| Automated local tests | Review/version guards, HTTP routes, simulated draft, export and read-only recovery | Simulated provider and DOM adapters; these tests are not the browser run below |
| [9 November observed browser run](SANDBOX_BROWSER_RUN_20261109.md) | Fresh external AI imports, real Sandbox OAuth, one unsent EUR 125 draft, matching read-back, revoked acceptance and read-only recovery after an edit | Manual AI import; assistant operated both test roles; no independent customer, provider-log export or new continuous video |
| Current video | Actual earlier 0.3.5 browser states, imported AI, review and simulator workflow | Sampled captures and edits; no continuous integrated live run |
| [19 October Sandbox run #1](https://github.com/carlosjunquerovila-afk/scopeproof/actions/runs/39273764876) and [receipt](../demo_evidence/sandbox_transport_20261019.json) | OAuth, one unsent EUR 125 draft and matching GET from source `5af9f89a780ea265f76fef26d9b9614b93d46f4f` | Earlier 0.3.4 core adapter; no browser, fresh model or this candidate |
| External ChatGPT import | Schema, criterion IDs, exact quotations and snapshot checked | No evidence-truth or model-authorship guarantee |
| Optional Ollama / OpenAI code | Separately configurable adapters | No successful model run in this audit |

The automated tests, current video and 19 October runner are separate from the newly observed 9 November browser workflow. The historical Sandbox runner is one-shot; do not redispatch it.

## Optional real Sandbox path

Follow [the README's private Sandbox setup](../README.md#connect-paypal-sandbox-privately). Use your own free Developer Sandbox app and generated seller/buyer test accounts. Start `python app.py --sandbox --workspace ../scopeproof-judge-sandbox`; connect privately, save evidence, obtain/import fresh analysis, review explicitly, confirm one draft and inspect read-back. Keep credentials out of the repository and recording. No send or payment is implemented.

The [9 November observation](SANDBOX_BROWSER_RUN_20261109.md) exercised this browser path on the user's Windows computer, including the new read-only button against a real Sandbox draft after an edit. Three fresh responses were generated in an external ChatGPT conversation and imported; **no in-app LLM call or independent customer acceptance was demonstrated**. The provider result was observed through the application and audited adapter, without an independent PayPal dashboard-log export. Without Sandbox credentials, judges can fully exercise only the simulator path.

## Freeze and history

The [deadline](https://paypalaihackathon.devpost.com/rules) is **12 November 2026, 21:00 Europe/Madrid**. The organizer's 5 November reminder asks entrants to keep access active until 21 December and leave linked repository/video/materials unchanged after closing. Freeze reviewed source before the deadline. External changes require owner approval.

Earlier `README_JUDGES.md`, `DEVPOST_STORY.md`, release notes and manifests are historical. This guide is the current entry point. No customer savings, production certification, independent competitive superiority or award is claimed.
