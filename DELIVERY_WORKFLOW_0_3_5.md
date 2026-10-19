# ScopeProof 0.3.5 — delivery workflow candidate

This change completes a usable local handover: the studio enters a milestone and delivery report, reviews the saved version, prepares a draft, then downloads a readable record containing those exact saved inputs and their outcome. The downloaded HTML opens without a server, login, network connection or extra packages and has print styles for saving to PDF.

It extends the existing Python application. It is not a new hosted product, a replacement for the PayPal integration or a claim of production readiness. PayPal remains Sandbox-only; default mode still uses the simulator. No real payment or invoice-send capability is added.

## What the user does

1. Start `python app.py` and use the private local merchant session.
2. Enter the agreed milestone name, integer-cent price, currency and acceptance criteria. Save the scope.
3. Enter the delivery report and save that version. Locate passages locally or import a review for the current version through the existing interface.
4. Open the separate local review session, inspect each criterion and explicitly accept the current version.
5. Return to the merchant session and prepare the draft in the displayed environment.
6. Choose **Download delivery report**. The file includes the agreed amount, parties, criterion findings and quotations, human-review state, evidence, draft state and saved-version fingerprint. Open it in a normal browser to read or print it.

Downloading is allowed before acceptance as well: the record then states that review is pending. Analysis alone never marks the human decision accepted. Unsaved scope or report edits block the download until saved or discarded.

## Changes after acceptance

Saving new evidence revokes the prior acceptance through the existing workflow. The export labels any existing draft as belonging to the earlier version, displays its original amount and fingerprint, and does not apply that draft to the current delivery.

Expired acceptance is also marked. After a process restart, earlier provider verification is labelled historical until explicitly re-read. An unknown provider outcome stays unresolved; export does not retry creation or contact any provider.

## Portable record verification

The HTML contains an inert, base64-encoded data record. Every visible field is escaped; there are no executable scripts, external images, fonts, links, forms or tracking requests. The file supplies a restrictive Content Security Policy.

The offline checker parses the embedded data and reconstructs the full visible document. Changing only a visible amount or acceptance label is therefore detected, even if the embedded checksum remains unchanged.

```sh
python tools/verify_delivery.py path/to/downloaded-report.html
```

This checks internal consistency. It does not authenticate a customer, prove that supplied evidence is true, provide independent notarization, or prevent an editor from replacing both data and checksum. A local review link remains a capability, not a verified identity or legal signature. The rendering contract is identified by `scopeproof-delivery/1`; a future rendering change must introduce a new format and retain the old verifier if old exports are to remain verifiable.

The document contains the project and contact details entered in the saved workspace. Review it before sharing. Credentials, session capabilities, approval envelopes and private signing keys are not copied into it.

## Reproduce the fresh project flow

```sh
python tools/demo_delivery_flow.py --output ../scopeproof-delivery-run
```

This starts the actual loopback HTTP server in a temporary workspace, creates a new project identity and submits a new EUR 299 scope. It checks that a premature draft is refused, then saves corrected evidence, performs explicit scripted review, creates and re-reads one simulated draft, exports the accepted record, changes the evidence and exports a pending-review record bound to the earlier draft. It downloads three actual HTML records plus `flow_receipt.json` through the real application endpoint.

The receipt identifies the transport, requests, version fingerprints and exported-file hashes. The scenario uses synthetic supplied text, local lexical passage search and a scripted local reviewer. It makes no external requests and does not exercise an ordinary browser, new AI inference, a customer, PayPal or payment.

## Checks for this change

- The previously published 0.3.4 baseline was reproduced: 202 Python tests and five HTTP fault scenarios passed before editing.
- Twelve additional regressions cover current versus prior versions, expiration, restarted sessions, unknown provider outcomes, injected HTML, visible-content tampering, capability omission, export authorization and the real HTTP export route.
- Three added controller checks cover unsaved-text protection, delivery downloads using the server's document and filename, and failure without a partial download.
- The existing test runner includes the new regressions. JavaScript-controller checks execute the real `static/app.js` with explicit DOM/HTTP adapters; they are not browser rendering evidence.

The final receipt and test counts are recorded separately from the earlier PayPal Sandbox receipt. No one-shot Sandbox run should be redispatched to validate this document-only change.

## Commercial boundary

This handover can support a supervised studio pilot while production invoicing stays in the studio's existing system. It does not establish demand, sales, savings or a validated price. The earlier proposed EUR 99 pilot remains a hypothesis to test with actual customers.
