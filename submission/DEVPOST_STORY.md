## Inspiration
A studio can deliver the work and still struggle to answer a basic question: which version did the client accept? Evidence, acceptance and invoice preparation often live in different places. ScopeProof brings that handoff into one narrow, inspectable workflow.

## What it does
ScopeProof connects an agreed milestone, textual delivery evidence, explicit review and a PayPal Sandbox invoice-draft workflow. The AI proposes findings with exact quotations. A reviewer decides whether to accept each criterion for the current version. Changing the evidence or agreed scope invalidates that acceptance.

Billing keeps the agreed integer-cent amount. The model cannot approve a milestone, set a price or create an invoice. If a draft-creation response is lost, the app records an unknown outcome and uses read-only reconciliation instead of blindly repeating creation.

The default environment is visibly labelled LOCAL SIMULATOR — NOT PAYPAL. The prototype does not send invoices or collect payments. Review links authorize a local session; they do not verify a customer's identity.

## How we built it
Python 3.11+, SQLite and a small HTML/CSS/JavaScript interface. The local server uses revision checks, short-lived review capabilities, durable billing intents and a PayPal Invoicing v2 Sandbox adapter for OAuth, draft creation and direct read-back.

The AI interaction is explicit: export a snapshot-bound prompt, obtain a structured answer from an external AI tool, and import it. The application checks the schema, criterion IDs, current snapshot and literal quotes. Imported authorship is not authenticated. Local lexical retrieval is labelled separately and is not presented as an LLM.

## What we demonstrated
On October 16, two fresh ChatGPT responses were generated from prompts exported by the application. Actual loopback HTTP then imported those responses and exercised the synthetic workflow in 16 requests. The incomplete report left staging contact and accessibility checks missing, including in the presence of an instruction embedded in the evidence to mark everything passed. The corrected report supported all three criteria, while approval remained a separate action.

A simulated operator accepted the current snapshot. Draft creation and a retry produced exactly one simulated invoice. Editing evidence revoked approval, rejected the old AI result and review link, and blocked another draft without a new review. The original fresh-generation run used 0.3.2; its frozen responses were successfully replayed on 0.3.3 and 0.3.4. The latter explicitly reconstructs the historical project identity inside a temporary simulator workspace; it does not change normal runtime identities or generate new model output. No model API was called by the app, and no real PayPal API call occurred in these runs.

## Challenges and improvements
We found and fixed an evidence-size mismatch before state mutation. Independent review within the development session also found that stale responses could overwrite unsaved evidence or an edited amount. Version 0.3.3 now preserves both editors, requires explicit save/discard and serializes operations while allowing continued typing.

Version 0.3.4 places the criterion, analysis reason, supporting quotation and human decision together in each review card. New workspaces receive distinct persisted identities, creation carries a stable request identifier, and explicit HTTP rejection is distinguished from an uncertain provider outcome. Neither result causes an automatic new creation request.

The recorded 0.3.4 verification passes 202 Python tests, five simulator HTTP fault scenarios, 21 JavaScript-controller checks and the 16-request historical-response replay. These are internal checks with controlled responses and DOM/transport adapters, not independent certification or full browser-to-Sandbox testing. Earlier version reports are retained with their original dates and scope.

## What's next
Complete and record one authenticated application-to-PayPal Sandbox create/read-back, publish the licensed source and the final English demo, and complete submission declarations. The current Devpost entry is a development draft.

For commercial validation, the first proposed customer is a small web studio. We have prepared a supervised pilot covering one project and up to three guided reviews, at an experimental price of EUR 99. No outreach, customer trial, sale or revenue has occurred. The test will measure review time, corrections and actual willingness to pay.
