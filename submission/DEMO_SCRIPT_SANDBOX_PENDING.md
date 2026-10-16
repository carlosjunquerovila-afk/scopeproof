# ScopeProof — Sandbox replacement segment

**NOT RECORDED. NOT A CLAIM OF COMPLETED INTEGRATION.** This segment replaces parts of the local script only after every relevant gate below has evidence. Do not call a signed-in PayPal browser or a successful OAuth request a completed invoice flow.

## Promotion gates

1. Execute the approved application build, record its exact version/hash and preserve the relevant test result.
2. Run a genuine model interaction on the displayed current evidence. Record provider/tool, model identifier if available, timing, input fingerprint and output. Manual external-tool use must be labelled as such; a saved answer replay must remain labelled replay.
3. Use authorized PayPal Sandbox test accounts and establish OAuth in the app's running process. Keep credentials off-camera.
4. Explicitly review the current version and confirm draft creation. Record the outbound operation as a Sandbox create, preserve its returned invoice ID privately, and read the invoice directly from the Sandbox API.
5. Match amount, currency, sender, recipient, invoice number and description. Record `DRAFT` status and the absence of any invoice-send or payment action.
6. Preserve a redacted receipt with build hash, UTC/Madrid timestamp, actual request outcomes and verified fields. Preserve the unredacted receipt privately when appropriate. Do not include credentials or access tokens.
7. Verify the public source reproduces the recorded application and the final video remains below three minutes. Confirm the final AI interaction is sufficiently meaningful under the organizer's rules.

## Replacement script — 45 seconds, approximately 100 spoken words

**Show the actual app and real successful read-back only if the gates pass.**

“This run uses PayPal Sandbox with test accounts. After reviewing the current version, I separately confirm creation of one invoice draft. The application creates it, then reads it directly from PayPal. It checks the amount, currency, sender, recipient, invoice number and description against the accepted scope. Here is the matching draft, with account identifiers redacted. The draft has not been sent, and no payment was captured. The earlier lost-response example was deliberately injected in our local simulator; this Sandbox run establishes the external create-and-read path. It does not establish production readiness or prove customer demand.”

## AI replacement — 20 seconds

Use only wording matching the recorded path:

- **Actual in-app inference:** “This is a fresh call to [actual provider/model] from the application on the displayed snapshot. It returns criterion-level findings and quotes. The deterministic checks validate the shape, references and version; a person still decides whether to accept.”
- **Actual external AI-tool interaction:** “I export this snapshot's prompt to [actual tool], obtain a fresh response, and import it here. ScopeProof checks references and version, but cannot authenticate the pasted response's author. A person still decides whether to accept.”

If no new inference occurred, retain the replay disclosure and do not use either replacement. Avoid implying that the application independently verifies the reported work.

## Short final-demo cut after evidence is available

| Time | Content |
|---|---|
| 00–15 | Target user's problem and fixed-price milestone. |
| 15–45 | Actual AI interaction with incomplete evidence; criterion and citation output. |
| 45–70 | New report, explicit current-version review and separate draft confirmation. |
| 70–115 | The real Sandbox replacement segment above. |
| 115–140 | Clearly separated local simulator lost-response and reconciliation segment. |
| 140–157 | Internal tests and one product limitation. |
| 157–170 | Measured pilot result if one exists; otherwise label the planned studio pilot as pending. |

The polished narrative must follow the captured evidence. Do not edit evidence to match the narrative.
