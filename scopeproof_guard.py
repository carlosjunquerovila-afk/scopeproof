"""ScopeProof: an offline draft-invoice preparation gate (prototype, not production).

Standard library only; no HTTP, PayPal calls, model inference or financial action.
Approval records are TRUSTED local inputs, not proof of a real authenticated human.
Evidence hashing proves byte consistency, NOT that an artifact fulfills a promise.
The eventual app must authenticate the approval, review evidence and call sandbox.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from contextlib import closing
from pathlib import Path
from typing import Mapping

VERSION = '0.1.1-explicit-db-close'
MAX_TOTAL_CENTS = 100_000_000
SANDBOX_BASE = 'https://api-m.sandbox.paypal.com'
ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')

class Refused(ValueError):
    pass

def need(ok: bool, reason: str) -> None:
    if not ok:
        raise Refused(reason)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode()

@dataclass(frozen=True)
class Milestone:
    id: str
    name: str
    amount_cents: int
    required_evidence: tuple[str, ...]

@dataclass(frozen=True)
class Scope:
    project_id: str
    revision: int
    currency: str
    recipient: str
    sender: str
    milestones: tuple[Milestone, ...]

    def validate(self) -> None:
        need(type(self.project_id) is str and bool(ID_PATTERN.fullmatch(self.project_id)), 'Invalid project ID')
        need(type(self.revision) is int and self.revision > 0, 'Revision must be a positive integer')
        need(self.currency in ('EUR', 'USD'), 'Prototype supports EUR/USD only')
        for address in (self.recipient, self.sender):
            need(type(address) is str and len(address) <= 254 and bool(re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', address)), 'Invalid email')
        need(type(self.milestones) is tuple and 1 <= len(self.milestones) <= 20, 'Expected 1..20 milestones')
        ids = set(); total = 0
        for line in self.milestones:
            need(type(line) is Milestone, 'Invalid milestone type')
            need(type(line.id) is str and bool(ID_PATTERN.fullmatch(line.id)) and line.id not in ids, 'Invalid or duplicated milestone ID')
            ids.add(line.id)
            need(type(line.name) is str and 1 <= len(line.name) <= 200 and all(ord(c) >= 32 for c in line.name), 'Invalid milestone name')
            need(type(line.amount_cents) is int and 0 < line.amount_cents <= MAX_TOTAL_CENTS, 'Use positive integer cents')
            need(type(line.required_evidence) is tuple and 1 <= len(line.required_evidence) <= 20 and len(set(line.required_evidence)) == len(line.required_evidence), 'Invalid evidence requirements')
            need(all(type(e) is str and bool(ID_PATTERN.fullmatch(e)) for e in line.required_evidence), 'Invalid evidence ID')
            total += line.amount_cents
        need(total <= MAX_TOTAL_CENTS, 'Scope exceeds prototype amount cap')

    def fingerprint(self) -> str:
        self.validate()
        return digest(canonical(asdict(self)))

@dataclass(frozen=True)
class Approval:
    scope_sha256: str
    milestone_id: str
    reviewed_evidence: tuple[tuple[str, str], ...]
    approved_by: str
    accepted: bool


def prepare_draft(scope: Scope, milestone_id: str, artifacts: Mapping[str, bytes],
                  approval: Approval, *, environment: str = 'sandbox') -> dict:
    """Prepare a JSON payload ONLY. Trusted approvals must be authenticated upstream.

    A model supplies only a proposed milestone ID. Its text cannot set the amount,
    currency, recipient, seller, approval or whether evidence is accepted.
    """
    need(environment == 'sandbox', 'Only sandbox preparation is allowed')
    scope_sha = scope.fingerprint()
    need(type(milestone_id) is str, 'Milestone ID must be a string')
    found = [m for m in scope.milestones if m.id == milestone_id]
    need(len(found) == 1, 'Unknown milestone; no invented invoice lines')
    line = found[0]
    need(type(approval) is Approval, 'Approval record required')
    need(approval.accepted is True, 'Explicit acceptance required')
    need(approval.scope_sha256 == scope_sha and approval.milestone_id == line.id, 'Approval is stale or belongs to another scope')
    need(type(approval.approved_by) is str and bool(approval.approved_by.strip()) and len(approval.approved_by) <= 200, 'Reviewer required')
    need(type(approval.reviewed_evidence) is tuple, 'Evidence review must be a tuple')
    need(all(type(pair) is tuple and len(pair) == 2 and all(type(v) is str for v in pair) for pair in approval.reviewed_evidence), 'Malformed evidence approval')
    reviewed = dict(approval.reviewed_evidence)
    need(len(reviewed) == len(approval.reviewed_evidence), 'Duplicated evidence approval')
    need(set(reviewed) == set(line.required_evidence), 'Every required artifact must have been reviewed')
    for evidence_id in line.required_evidence:
        need(evidence_id in artifacts and type(artifacts[evidence_id]) is bytes, 'Missing artifact bytes')
        data = artifacts[evidence_id]
        need(0 < len(data) <= 10 * 1024 * 1024, 'Artifact size out of bounds')
        need(bool(re.fullmatch(r'[0-9a-f]{64}', reviewed[evidence_id])) and reviewed[evidence_id] == digest(data), 'Artifact changed after review')
    value = f'{line.amount_cents // 100}.{line.amount_cents % 100:02d}'
    # Same project+milestone is one economic event even across revisions.
    # Changes require explicit reconciliation, not a silent new billing attempt.
    billing_key = digest(canonical([scope.project_id, line.id]))
    invoice_number = 'SP-' + billing_key[:20]
    payload = {
        'detail': {'currency_code': scope.currency, 'invoice_number': invoice_number,
                   'note': 'ScopeProof sandbox prototype. No real payment requested.'},
        'invoicer': {'email_address': scope.sender},
        'primary_recipients': [{'billing_info': {'email_address': scope.recipient}}],
        'items': [{'name': line.name, 'quantity': '1',
                   'unit_amount': {'currency_code': scope.currency, 'value': value}}]
    }
    return {'status': 'LOCAL_DRAFT_PREPARED_NOT_CREATED_IN_PAYPAL', 'version': VERSION,
            'sandbox_endpoint': SANDBOX_BASE + '/v2/invoicing/invoices',
            'scope_sha256': scope_sha, 'milestone_id': line.id, 'billing_key': billing_key,
            'payload': payload, 'payload_sha256': digest(canonical(payload)),
            'evidence_sha256': reviewed, 'approval_source': 'trusted_local_record_not_authenticated',
            'external_calls': 0, 'funds_moved': False}


def reserve_once(database: str | Path, draft: dict) -> dict:
    """Reserve locally with a UNIQUE key. No assertion of PayPal idempotency.

    Pending/unknown network outcomes would require reconciliation before retrying.
    This prototype never sends the draft and cannot record it as remotely created.
    """
    need(draft.get('status') == 'LOCAL_DRAFT_PREPARED_NOT_CREATED_IN_PAYPAL', 'Unexpected draft status')
    need(draft.get('payload_sha256') == digest(canonical(draft.get('payload'))), 'Draft payload was modified')
    key = draft.get('billing_key'); sha = draft['payload_sha256']
    need(type(key) is str and bool(re.fullmatch(r'[0-9a-f]{64}', key)), 'Invalid billing key')
    with closing(sqlite3.connect(database, timeout=5)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS prepared (billing_key TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL, status TEXT NOT NULL)')
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload_sha256,status FROM prepared WHERE billing_key=?', (key,)).fetchone()
            if row is not None:
                need(row[0] == sha, 'Existing billing event differs: explicit reconciliation required')
                return {'status': 'ALREADY_PREPARED_LOCALLY', 'external_calls': 0}
            db.execute('INSERT INTO prepared VALUES (?,?,?)', (key, sha, 'PREPARED_LOCALLY'))
    return {'status': 'PREPARED_LOCALLY', 'external_calls': 0}


def example() -> tuple[Scope, dict[str, bytes], Approval]:
    scope = Scope('demo-web-project', 1, 'EUR', 'buyer@example.com', 'seller@example.com',
                  (Milestone('homepage', 'Homepage delivery', 12500, ('acceptance-report',)),))
    artifacts = {'acceptance-report': b'Controlled demo: client reviewed homepage v1.'}
    approval = Approval(scope.fingerprint(), 'homepage', (('acceptance-report', digest(artifacts['acceptance-report'])),), 'demo-reviewer', True)
    return scope, artifacts, approval

if __name__ == '__main__':
    scope, artifacts, approval = example()
    print(json.dumps(prepare_draft(scope, 'homepage', artifacts, approval), indent=2))
