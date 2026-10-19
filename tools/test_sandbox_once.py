"""Local-only tests for the one-shot guard and public redaction boundary."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sandbox_once as s


def context():
    return {
        "GITHUB_REPOSITORY": s.REPOSITORY,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_RUN_NUMBER": "1",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_RUN_ID": "456789",
        "GITHUB_SHA": "a" * 40,
    }


def history():
    return {"total_count": 1, "workflow_runs": [{
        "id": 456789, "run_number": 1, "run_attempt": 1,
        "event": "workflow_dispatch", "head_branch": "main", "head_sha": "a" * 40,
    }]}


class OneShotTests(unittest.TestCase):
    def test_only_the_first_current_run_passes(self):
        s.require_only_current_run(history(), context())

    def test_reruns_and_later_dispatches_are_blocked(self):
        for field, value in (("GITHUB_RUN_ATTEMPT", "2"), ("GITHUB_RUN_NUMBER", "2"),
                             ("GITHUB_REF", "refs/heads/feature"),
                             ("GITHUB_REPOSITORY", "attacker/fork"),
                             ("GITHUB_EVENT_NAME", "push")):
            with self.subTest(field=field):
                env = context()
                env[field] = value
                with self.assertRaises(s.Refused):
                    s.require_only_current_run(history(), env)

    def test_api_history_omission_unknown_and_prior_runs_block(self):
        bad = [None, {}, {"total_count": 0, "workflow_runs": []},
               {"total_count": 2, "workflow_runs": history()["workflow_runs"]},
               {"total_count": True, "workflow_runs": history()["workflow_runs"]},
               {"total_count": 1, "workflow_runs": []},
               {"total_count": 1, "workflow_runs": [{**history()["workflow_runs"][0], "id": 3}]},
               {"total_count": 1, "workflow_runs": [{**history()["workflow_runs"][0],
                                                       "head_sha": "b" * 40}]},
               {"total_count": 1, "workflow_runs": [{**history()["workflow_runs"][0],
                                                       "run_attempt": 2}]},
               {"total_count": 1, "workflow_runs": [history()["workflow_runs"][0],
                                                      history()["workflow_runs"][0]]}]
        for entry in bad:
            with self.subTest(entry=entry), self.assertRaises(s.Refused):
                s.require_only_current_run(entry, context())

    def test_api_failure_never_advances_to_draft(self):
        output = io.StringIO()
        with patch.object(s, "get_history", side_effect=RuntimeError("SECRET_SENTINEL")), \
             patch.object(s, "create_and_check") as draft, redirect_stdout(output):
            code = s.main(["preflight"], context())
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue().strip(), "ONE_SHOT_GATE_BLOCKED")
        draft.assert_not_called()

    def test_only_generated_distinct_sandbox_parties_allowed(self):
        env = {name: "dummy-id-or-secret" for name in s.SECRET_NAMES}
        env.update(PAYPAL_SANDBOX_SELLER_EMAIL="sb-seller@business.example.com",
                   PAYPAL_SANDBOX_BUYER_EMAIL="sb-buyer@personal.example.com")
        self.assertEqual(s.validate_parties(env)[0], "sb-seller@business.example.com")
        for buyer in ("customer@gmail.com", "sb-buyer@example.com", "", "SB@business.example.com"):
            with self.subTest(buyer=buyer), self.assertRaises(s.Refused):
                s.validate_parties({**env, "PAYPAL_SANDBOX_BUYER_EMAIL": buyer})

    def test_success_report_whitelists_sensitive_result_and_environment(self):
        marker = "PRIVATE_SECRET_SENTINEL"
        private_id = "INV2-PRIVATE_ID_SENTINEL"
        env = {**context(), "PAYPAL_SANDBOX_CLIENT_SECRET": marker,
               "PAYPAL_SANDBOX_SELLER_EMAIL": "sb-private@business.example.com"}
        result = {"status": "VERIFIED_DRAFT", "provenance": "PAYPAL_SANDBOX",
                  "recipient_notified_by_this_app": False, "payment_attempted": False,
                  "invoice_id": private_id, "billing_key": marker, "provider_body": env["PAYPAL_SANDBOX_SELLER_EMAIL"]}
        with tempfile.TemporaryDirectory() as folder:
            env["GITHUB_STEP_SUMMARY"] = str(Path(folder) / "summary")
            output = io.StringIO()
            with patch.object(s, "create_and_check", return_value=result), redirect_stdout(output):
                code = s.main(["draft", folder], env)
            public = output.getvalue() + Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        self.assertEqual(code, 0)
        self.assertIn('"authenticated_post_and_direct_get_verified": true', public)
        for private in (marker, private_id, env["PAYPAL_SANDBOX_SELLER_EMAIL"]):
            self.assertNotIn(private, public)

    def test_exception_containing_secrets_is_never_printed(self):
        marker = "PRIVATE_SECRET_SENTINEL"
        env = {**context(), "PAYPAL_SANDBOX_CLIENT_SECRET": marker}
        with tempfile.TemporaryDirectory() as folder:
            env["GITHUB_STEP_SUMMARY"] = str(Path(folder) / "summary")
            output = io.StringIO()
            with patch.object(s, "create_and_check", side_effect=RuntimeError(marker)), \
                 redirect_stdout(output):
                code = s.main(["draft", folder], env)
            public = output.getvalue() + Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        self.assertEqual(code, 2)
        self.assertNotIn(marker, public)
        self.assertIn('"status": "FAILED_CLOSED"', public)

    def test_unknown_outcome_never_becomes_success(self):
        report = s.receipt({"status": "UNKNOWN", "invoice_id": "INV2-SECRET",
                            "provenance": "PAYPAL_SANDBOX"})
        self.assertFalse(report["authenticated_post_and_direct_get_verified"])
        self.assertNotIn("INV2-SECRET", str(report))

    def test_inconsistent_verified_draft_is_failed_closed(self):
        for changed in ({"provenance": "INJECTED_TEST_TRANSPORT"},
                        {"recipient_notified_by_this_app": True},
                        {"payment_attempted": True}):
            result = {"status": "VERIFIED_DRAFT", "provenance": "PAYPAL_SANDBOX",
                      "recipient_notified_by_this_app": False, "payment_attempted": False,
                      **changed}
            with self.subTest(changed=changed):
                report = s.receipt(result)
                self.assertEqual(report["status"], "FAILED_CLOSED")
                self.assertFalse(report["authenticated_post_and_direct_get_verified"])


if __name__ == "__main__":
    unittest.main()
