# Presentation package — final integration notes

This folder belongs at `submission/` in ScopeProof 0.3.4. The fresh-generation trace, prompts, saved responses and replay harness belong at `demo_evidence/`, relative to the application root. No video or external customer contact was created by this package.

- `README_JUDGES.md` is synchronized with the final English application README during packaging. `VERIFICATION_0_3_4.txt` records 202 Python tests, five HTTP fault scenarios, 21 JavaScript-controller checks and a 16-request historical-response replay, all passing. Historical 0.3.3 reports retain their original version.
- `NARRATION_LOCAL.txt` and `DEMO_SCRIPT_LOCAL.md` describe the current review interface and replaying actual external AI responses, not fresh inference during filming. The script is a recording plan, not completed footage.
- `DEMO_REPORT_INCOMPLETE.txt` and `DEMO_REPORT_COMPLETE.txt` preserve the exact synthetic text from exported prompts. Save them as revisions 2 and 3 in a fresh workspace to match the stored response snapshots. Do not use the app's different older complete-sample button for this particular script.
- `DEMO_SCRIPT_SANDBOX_PENDING.md` remains conditional on actual authenticated create/read-back evidence. No successful Sandbox round-trip is claimed.
- `STORYBOARD.html` is a white editorial plan, not product footage.
- The original fresh AI run used 0.3.2 and made 16 actual HTTP requests. Saved-output replays passed on 0.3.3 and 0.3.4; neither made a new inference. `demo_evidence/replay_0_3_4.json` identifies the temporary simulator fixture with the historical project identity. Original receipts and model responses remain unchanged. The application made no model API calls, and all invoices were simulated. The earlier `demo_evidence/manifest.json` is retained with its historical harness hash; `MANIFEST_0_3_4.json` describes the current directory.
- `REHEARSAL_CHECK.json` is the earlier 0.3.2 in-process rehearsal of the default sample/lost-response path. It is retained as explicitly older evidence; it is not the fresh HTTP run or the current main-video sequence.
- The commercial hypothesis is now €99 per supervised pilot, replacing the earlier €49 planning figure. Neither price has been validated; no sales are recorded.

Before final competition submission, record real application footage and real Sandbox evidence and keep tokens/credentials private. Source may be published with those gates explicitly pending. Verify its public file hashes and recompute this package manifest after any edits. Publish only source, assets, tests, documentation and intentional synthetic evidence; exclude private workspaces, databases, credentials and unsanitized local records.
