#!/usr/bin/env python3
"""Manual, one-shot Sandbox transport test for ScopeProof v0.3.4.

Public logs and the step summary have an explicit allowlist. The private runner
workspace is ephemeral; uncertain outcomes require read-only investigation in
the PayPal Sandbox dashboard. Do not rerun to resolve a failure.
"""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request


REPOSITORY = "carlosjunquerovila-afk/scopeproof"
WORKFLOW = "scopeproof-sandbox-once.yml"
SOURCE_COMMIT = "5af9f89a780ea265f76fef26d9b9614b93d46f4f"
PROJECT_ID = "scopeproof-gha-draft-v034-20261019"
SECRET_NAMES = (
    "PAYPAL_SANDBOX_CLIENT_ID", "PAYPAL_SANDBOX_CLIENT_SECRET",
    "PAYPAL_SANDBOX_SELLER_EMAIL", "PAYPAL_SANDBOX_BUYER_EMAIL",
)
SAFE_STATES = frozenset((
    "VERIFIED_DRAFT", "UNKNOWN", "CREATE_REJECTED", "REVIEW_REQUIRED",
    "CREATED_UNVERIFIED", "IN_FLIGHT", "READBACK_UNAVAILABLE",
))


class Refused(Exception):
    """Only a fixed public error code may be emitted by the command wrapper."""


def require_context(env: dict[str, str]) -> int:
    if (env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_REF") != "refs/heads/main"
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or env.get("GITHUB_RUN_NUMBER") != "1"
            or env.get("GITHUB_RUN_ATTEMPT") != "1"
            or not re.fullmatch(r"[1-9][0-9]*", env.get("GITHUB_RUN_ID", ""))
            or not re.fullmatch(r"[a-f0-9]{40}", env.get("GITHUB_SHA", ""))):
        raise Refused()
    return int(env["GITHUB_RUN_ID"])


def require_only_current_run(history: object, env: dict[str, str]) -> None:
    """Fail closed for every unknown API/history shape, including an empty list."""
    run_id = require_context(env)
    if type(history) is not dict or type(history.get("total_count")) is not int \
            or history["total_count"] != 1:
        raise Refused()
    runs = history.get("workflow_runs")
    if type(runs) is not list or len(runs) != 1 or type(runs[0]) is not dict:
        raise Refused()
    current = runs[0]
    if (type(current.get("id")) is not int or current["id"] != run_id
            or type(current.get("run_number")) is not int or current["run_number"] != 1
            or type(current.get("run_attempt")) is not int or current["run_attempt"] != 1
            or current.get("event") != "workflow_dispatch"
            or current.get("head_branch") != "main"
            or current.get("head_sha") != env["GITHUB_SHA"]):
        raise Refused()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise Refused()


def get_history(env: dict[str, str]) -> object:
    token = env.get("GH_ACTIONS_READ_TOKEN", "")
    if not token:
        raise Refused()
    url = f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/runs?per_page=2"
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=15) as response:
        if response.status != 200:
            raise Refused()
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise Refused()
    return json.loads(raw)


def validate_parties(env: dict[str, str]) -> tuple[str, str]:
    if not all(env.get(name) for name in SECRET_NAMES):
        raise Refused()
    seller = env["PAYPAL_SANDBOX_SELLER_EMAIL"]
    buyer = env["PAYPAL_SANDBOX_BUYER_EMAIL"]
    # Generated Sandbox test accounts only. Never accept an ordinary email.
    pattern = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+"
    if (not re.fullmatch(pattern, seller) or not re.fullmatch(pattern, buyer)
            or len(seller) > 254 or len(buyer) > 254
            or not seller.lower().endswith("@business.example.com")
            or not buyer.lower().endswith("@personal.example.com")
            or seller.lower() == buyer.lower()):
        raise Refused()
    return seller, buyer


def validate_source(source: Path) -> None:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source,
                            text=True, capture_output=True, check=True).stdout.strip()
    if commit != SOURCE_COMMIT:
        raise Refused()
    changes = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             cwd=source, text=True, capture_output=True, check=True).stdout
    if changes.strip():
        raise Refused()


def create_and_check(source: Path, env: dict[str, str]) -> dict:
    """Call the pinned v0.3.4 transport once; never retry a POST on errors."""
    seller, buyer = validate_parties(env)
    validate_source(source)
    sys.path.insert(0, str(source))
    import scopeproof_bridge as bridge
    import scopeproof_guard as guard

    # The artifact and review are synthetic and explicitly labelled as such.
    scope, artifacts, approval = guard.example()
    scope = replace(scope, project_id=PROJECT_ID, recipient=buyer, sender=seller)
    scope.validate()
    approval = replace(approval, scope_sha256=scope.fingerprint(),
                       approved_by="synthetic-local-demo-review")
    draft = bridge.safe_draft(scope, "homepage", artifacts, approval)
    signer = bridge.LocalSigner(os.urandom(32))
    envelope = signer.issue(draft, reviewer="synthetic-local-demo-review", accepted=True)
    paypal = bridge.SandboxPayPal.from_env()
    # No private ledger, signer or full receipt leaves the GitHub-hosted runner.
    with tempfile.TemporaryDirectory(prefix="scopeproof-sandbox-once-") as folder:
        ledger = bridge.Ledger(Path(folder) / "sandbox-ledger.db")
        return bridge.execute(scope, "homepage", artifacts, approval,
                              envelope, signer, ledger, paypal)


def receipt(result: object) -> dict:
    """Fixed public allowlist, even if a provider result contains private data."""
    state = result.get("status") if type(result) is dict else None
    state = state if type(state) is str and state in SAFE_STATES else "FAILED_CLOSED"
    verified = (state == "VERIFIED_DRAFT"
                and result.get("provenance") == "PAYPAL_SANDBOX"
                and result.get("recipient_notified_by_this_app") is False
                and result.get("payment_attempted") is False)
    if state == "VERIFIED_DRAFT" and not verified:
        state = "FAILED_CLOSED"
    return {
        "source_commit": SOURCE_COMMIT,
        "status": state,
        "authenticated_post_and_direct_get_verified": bool(verified),
        "synthetic_local_review": True,
        "invoice_sent_by_this_app": False,
        "payment_attempted_by_this_app": False,
    }


def emit(report: dict, env: dict[str, str]) -> None:
    serialized = json.dumps(report, sort_keys=True)
    print(serialized, flush=True)
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("## ScopeProof Sandbox draft validation\n\n```json\n")
            output.write(json.dumps(report, indent=2, sort_keys=True))
            output.write("\n```\n")
            output.write("Synthetic local review and transport evidence only; "
                         "no customer approval or fresh model inference. "
                         "Do not rerun after failure or an unknown outcome.\n")


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    if len(argv) == 1 and argv[0] == "preflight":
        try:
            require_context(env)
            require_only_current_run(get_history(env), env)
        except Exception:
            print("ONE_SHOT_GATE_BLOCKED", flush=True)
            return 2
        print("ONE_SHOT_GATE_PASSED", flush=True)
        return 0
    if len(argv) == 2 and argv[0] == "draft":
        try:
            require_context(env)
            result = create_and_check(Path(argv[1]).resolve(strict=True), env)
            report = receipt(result)
        except Exception:
            # Never stringify an exception: provider responses can echo secrets.
            report = receipt(None)
        emit(report, env)
        return 0 if report["authenticated_post_and_direct_get_verified"] else 2
    print("INVALID_MODE", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
