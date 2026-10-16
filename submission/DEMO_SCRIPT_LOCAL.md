# ScopeProof 0.3.4 — demonstration production plan

**Script only. No footage or real PayPal Sandbox round-trip is established by this file.** Target final edit: **165–175 seconds**. Record the actual application. The final narrative must follow captured execution evidence.

## The decision to demonstrate

A small web studio has a fixed €125 website milestone. Its reviewer needs to connect the agreed criteria to the delivery report before accepting a version and preparing a draft. Show the distinction between a tested outcome and a promise, an appearance, or an outstanding check.

The useful AI moment is specific: a paraphrase of three viewport tests provides supporting text, while “the form looks correct” does not establish a successful staging submission. An empty issue list does not establish that an accessibility assessment happened. The model proposes findings; a person reviews the work and accepts each criterion.

## Preferred final recording — only after integration evidence exists

| Time | Actual capture required | Message |
|---|---|---|
| 00–15 | Agreed €125 milestone, current saved version and three criteria. Keep the environment visible. | A studio needs a reviewable handoff before preparing its invoice. |
| 15–45 | Generate an actual fresh AI response from the displayed connected snapshot, then show its criterion-level findings and quotations. Identify the actual tool/model and whether the interaction is external. | Semantic support, negation and missing checks require interpretation; findings are not acceptance. |
| 45–75 | Save the corrected synthetic report; obtain its new matching response. In the separate review session, inspect and explicitly accept each criterion and this version. | The reviewed version is explicit. The local session does not establish customer identity. |
| 75–115 | Separately confirm one real PayPal Sandbox draft. Show the application's actual direct read-back and matching fields, with private identifiers redacted. | The agreed amount reaches one provider draft; nothing was sent or paid. |
| 115–140 | Save a report change and show that the earlier acceptance no longer applies. | A changed delivery needs a new review. |
| 140–170 | Return to the readable criteria and provider result; close on intended studio use and remaining supervised user validation. | The agreement, reviewed evidence and draft are connected to a version. No customer savings or revenue is claimed. |

Keep the review summary and each finding/citation together in the frame. The count of supported criteria is an analysis summary, not an approval score. Do not use a green “complete” graphic for a model finding.

## Order of operations for a real Sandbox recording

1. Start a new, explicitly separate Sandbox workspace and authenticate using authorized test accounts, keeping credentials off-camera. **Connect before exporting any AI prompt.** Connecting changes sender/recipient and the snapshot, increments the evidence revision and clears earlier analysis/acceptance.
2. Save the exact report intended for the recording; export its current prompt. Generate a fresh answer using the actual AI route being demonstrated. Do not modify a response fingerprint to make an old answer fit.
3. Capture the ordinary-browser flow through explicit review, separate draft confirmation, successful creation and direct read-back. Preserve the build hash, UTC timestamp and sanitized request outcomes in a receipt.
4. Confirm the returned draft matches amount, currency, sender, recipient, invoice number and description. Preserve the `DRAFT` status. Do not send an invoice or capture payment to make this draft-only demonstration look more complete.
5. If the provider rejects creation, the real result is a rejection. The UI must show the sanitized HTTP status when available, disable another creation and offer no reconciliation for that rejected attempt. Stop the success segment; investigate without inventing a receipt.
6. Record version invalidation after the successful segment. An earlier provider record remains historical; it does not establish acceptance of newly edited evidence.
7. Use the actual captured outcome to select the conditional narration in `NARRATION_LOCAL.txt`. Publish only after checking the source matches the recording, secrets are absent and the video is under three minutes.

## Local fallback rehearsal — visibly a simulator

If the integration gate is still open, rehearse the same product story in the local simulator and use the default local narration. Keep **LOCAL SIMULATOR · NOT PAYPAL** and `INV2-MOCK-*` visible. This rehearsal does not satisfy the missing real-provider proof.

The frozen external-AI evidence was generated on runtime `0.3.2-evidence-limits`; its saved-output HTTP replay passed on `0.3.3-edit-safety`. The new `demo_evidence/replay_0_3_4.json` separately records 16 passing HTTP requests on `0.3.4-sandbox-identity`, reconstructing the historical project identity only in a temporary simulator fixture. None of the replays is new inference. The app made no model API call in those recorded runs. The provider and review actor were simulated, and the reports were synthetic.

For automated reproduction, run `python demo_evidence/run_demo.py --app . --replay --output ../scopeproof-local-replay.json` from the repository root. The harness retains the exact historical report sequence and explicitly reconstructs its legacy project identity inside a temporary simulator workspace. A normal new 0.3.4 workspace has a different identity, so simply importing these saved responses into the ordinary UI must fail its snapshot check. For browser footage in a new workspace, obtain responses to that workspace's actual exported prompts and describe those executions accurately. Do not change response fingerprints or weaken checks to reuse historical responses. The app's **Use complete sample** button also loads a different older sample and is not interchangeable with the reports in this folder. The recorded harness replay does not constitute browser footage.

## Recording and editorial checks

- Capture the real browser application; a storyboard or DOM adapter is not product footage. If browser access to the loopback application is blocked, record that limitation and stop the footage attempt.
- Keep session capabilities, API credentials, account identifiers and sensitive evidence off-camera. Redact private pixels while preserving the result and environment labels.
- Label replay, cuts and fast-forwarded waits. Never splice a different provider record into a failed request or imply two separate snapshots are one transaction.
- The local review link is an access capability. Describe the demonstrated role as a local reviewer, without claiming verified customer identity or a contractual signature.
- Move the simulator fault laboratory, detailed internal test counts and implementation discussion to the README or an optional supplementary clip. Keep one concise statement of the product's relevant limits in the main video.
- Do not add customer quotes, time saved, paid pilots or sales unless separately observed and authorized for publication.
