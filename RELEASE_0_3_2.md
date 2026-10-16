# ScopeProof 0.3.2 — consistent evidence limits

This candidate continues the recovered 0.3.1 source. It does not claim a new PayPal integration.

## Reproduced defect and fix

Previously the workspace accepted and saved an ASCII report of 20,001 characters, but both lexical review and AI review import rejected it because the review validator permits at most 20,000 characters. This could leave a saved revision that the review workflow could not process.

Evidence updates now reject more than 20,000 Unicode characters or 50,000 UTF-8 bytes before changing the saved revision. The existing byte ceiling is preserved. The interface explains both limits and reports that a rejected edit has not changed the saved version. Oversized reports are never silently truncated.

Four regressions cover the ASCII boundary, ASCII overflow with snapshot preservation, the UTF-8 boundary, and UTF-8 overflow with snapshot preservation. The full inherited suite plus these regressions passes: 192 tests and the five inherited local HTTP fault scenarios. These test counts are software checks, not user studies, intelligence benchmarks or evidence of PayPal access.

## Verification boundary

No PayPal OAuth, external model API inference, real invoice, deployment, repository publication, video publication or hackathon submission was performed by this release. All provider tests use a labelled simulator. The separate frozen semantic evaluation uses a conversation agent and imported responses; it does not turn the application into a live model service.

Run `python app.py` for the local simulator. Run `python run_tests.py` for the checks. Python 3.11 or later is required; no dependencies are downloaded. Stop with Ctrl+C. Sandbox configuration still needs authorized credentials and a reachable network. This is a development candidate, not a production billing service.
