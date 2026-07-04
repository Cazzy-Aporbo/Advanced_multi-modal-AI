from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from .contracts import (
    PrivacyCategory,
    PrivacyCategorySummary,
    PrivacyCorpusAuditRequest,
    PrivacyCorpusAuditResponse,
    PrivacyDetectorKind,
    PrivacyDocumentAudit,
    PrivacyFinding,
    PrivacyReceipt,
    PrivacyRunRecord,
    PrivacySeverity,
    PrivacyTaxonomyResponse,
    PrivacyTextRequest,
    PrivacyTextResponse,
)

DETECTOR_VERSION = "privacy-membrane-2026.07"

LANGUAGE_HINTS: tuple[str, ...] = (
    "english",
    "filipino",
    "spanish",
    "french",
    "german",
    "italian",
    "portuguese",
    "dutch",
    "polish",
    "russian",
    "ukrainian",
    "japanese",
    "korean",
    "chinese",
    "hindi",
    "arabic",
    "vietnamese",
    "thai",
    "indonesian",
    "turkish",
)

SEVERITY_WEIGHT: dict[PrivacySeverity, float] = {
    "low": 0.15,
    "medium": 0.35,
    "high": 0.72,
    "critical": 1.0,
}


@dataclass(frozen=True)
class CategorySpec:
    category_id: str
    label: str
    severity: PrivacySeverity
    family: str
    description: str
    detector_kinds: tuple[PrivacyDetectorKind, ...]
    language_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DetectorRule:
    category_id: str
    expression: re.Pattern[str]
    confidence: float
    kind: PrivacyDetectorKind = "pattern"
    evidence: str = ""
    validator: Callable[[str], bool] | None = None


def privacy_taxonomy() -> PrivacyTaxonomyResponse:
    categories = [
        PrivacyCategory(
            category_id=item.category_id,
            label=item.label,
            severity=item.severity,
            family=item.family,
            description=item.description,
            detector_kinds=list(item.detector_kinds),
            language_notes=list(item.language_notes),
        )
        for item in CATEGORY_SPECS
    ]
    return PrivacyTaxonomyResponse(
        detector_version=DETECTOR_VERSION,
        category_count=len(categories),
        language_count=len(LANGUAGE_HINTS),
        deterministic_category_count=len({rule.category_id for rule in DETECTOR_RULES})
        + len(CONTEXT_LABELS),
        categories=categories,
        language_hints=list(LANGUAGE_HINTS),
        boundary_notes=[
            (
                "This lane performs local deterministic detection and masking. "
                "It does not claim trained-token classification."
            ),
            (
                "The recognizers favor high-signal evidence: checksums, explicit "
                "labels, keyed secrets, and structured identifiers."
            ),
            (
                "Broad person-name and street-address recognition is limited to "
                "context labels to avoid pretending that general NER is present."
            ),
            (
                "The store persists receipts and aggregate counts only; raw text "
                "and redacted text are returned to the caller but not saved."
            ),
        ],
    )


def deidentify_text(request: PrivacyTextRequest) -> tuple[PrivacyTextResponse, PrivacyRunRecord]:
    findings = _find_privacy_spans(request)
    redacted_text = _apply_redactions(
        request.text,
        findings,
        mode=request.masking_mode,
    )
    category_summaries = _category_summaries(findings)
    language_hints = _language_hints(request.text, request.languages, findings)
    receipt = _receipt(
        source_text=request.text,
        redacted_text=redacted_text,
        findings=findings,
        masking_mode=request.masking_mode,
        language_hints=language_hints,
    )
    risk_score = _risk_score(findings, len(request.text))
    highest_severity = _highest_severity(findings)
    response = PrivacyTextResponse(
        redacted_text=redacted_text,
        risk_score=risk_score,
        highest_severity=highest_severity,
        finding_count=len(findings),
        category_summaries=category_summaries,
        language_hints=language_hints,
        findings=findings,
        receipt=receipt,
        notes=_response_notes(findings),
    )
    run = _run_record(
        run_id=response.run_id,
        route="/v1/privacy/deidentify",
        purpose=request.purpose,
        tenant_id=request.tenant_id,
        document_count=1,
        responses=[response],
        notes=request.notes,
    )
    return response, run


def audit_corpus(request: PrivacyCorpusAuditRequest) -> PrivacyCorpusAuditResponse:
    responses: list[PrivacyTextResponse] = []
    audits: list[PrivacyDocumentAudit] = []
    for document in request.documents:
        child_request = PrivacyTextRequest(
            text=document.text,
            languages=document.languages,
            masking_mode=request.masking_mode,
            categories=request.categories,
            min_confidence=request.min_confidence,
            include_context=False,
            tenant_id=request.tenant_id,
            purpose=request.purpose,
        )
        response, _ = deidentify_text(child_request)
        responses.append(response)
        audits.append(
            PrivacyDocumentAudit(
                document_id=document.document_id,
                risk_score=response.risk_score,
                finding_count=response.finding_count,
                category_ids=[item.category_id for item in response.category_summaries],
                language_hints=response.language_hints,
                receipt=response.receipt,
                redacted_text=response.redacted_text,
            )
        )

    run = _run_record(
        run_id=_stable_digest([item.receipt.receipt_id for item in responses])[:32],
        route="/v1/privacy/corpus/audit",
        purpose=request.purpose,
        tenant_id=request.tenant_id,
        document_count=len(request.documents),
        responses=responses,
        notes=request.notes,
    )
    return PrivacyCorpusAuditResponse(
        run=run,
        document_audits=audits,
        category_summaries=_merge_category_summaries(
            summary for response in responses for summary in response.category_summaries
        ),
        notes=[
            (
                "Corpus audit returned redacted text to the caller and persisted "
                "only receipts plus aggregate counts."
            ),
            (
                "Use the receipts to compare revisions without putting clinical "
                "notes, tickets, or claims into the repository."
            ),
        ],
    )


def _find_privacy_spans(request: PrivacyTextRequest) -> list[PrivacyFinding]:
    allowed = {item.lower() for item in request.categories}
    findings: list[PrivacyFinding] = []
    for rule in DETECTOR_RULES:
        if allowed and rule.category_id not in allowed:
            continue
        for match in rule.expression.finditer(request.text):
            value = match.group(0)
            if rule.validator is not None and not rule.validator(value):
                continue
            confidence = rule.confidence
            if confidence < request.min_confidence:
                continue
            findings.append(
                _finding(
                    category_id=rule.category_id,
                    kind=rule.kind,
                    start=match.start(),
                    end=match.end(),
                    value=value,
                    confidence=confidence,
                    evidence=[rule.evidence or f"{rule.category_id} pattern matched"],
                    language_hints=_language_hints_for_span(value),
                    masking_salt=request.masking_salt,
                )
            )

    findings.extend(_context_label_findings(request))
    return _dedupe_overlaps(findings)


def _context_label_findings(request: PrivacyTextRequest) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    allowed = {item.lower() for item in request.categories}
    for label, category_id, languages in CONTEXT_LABELS:
        if allowed and category_id not in allowed:
            continue
        expression = re.compile(
            rf"(?i)(?:^|[\n,;])\s*{re.escape(label)}\s*[:=]\s*([^\n,;]{{2,96}})"
        )
        for match in expression.finditer(request.text):
            value = match.group(1).strip()
            if not _context_value_is_useful(value):
                continue
            start = match.start(1) + (len(match.group(1)) - len(match.group(1).lstrip()))
            end = start + len(value)
            findings.append(
                _finding(
                    category_id=category_id,
                    kind="context_label",
                    start=start,
                    end=end,
                    value=value,
                    confidence=0.82,
                    evidence=[f"explicit label '{label}' found before value"],
                    language_hints=list(languages),
                    masking_salt=request.masking_salt,
                )
            )
    return findings


def _finding(
    *,
    category_id: str,
    kind: PrivacyDetectorKind,
    start: int,
    end: int,
    value: str,
    confidence: float,
    evidence: list[str],
    language_hints: list[str],
    masking_salt: str,
) -> PrivacyFinding:
    spec = CATEGORY_BY_ID[category_id]
    return PrivacyFinding(
        finding_id=_stable_digest(
            {
                "category_id": category_id,
                "span_start": start,
                "span_end": end,
                "value_hash": _stable_digest(value),
                "salt": masking_salt,
            }
        )[:24],
        category_id=category_id,
        category_label=spec.label,
        detector_kind=kind,
        severity=spec.severity,
        span_start=start,
        span_end=end,
        confidence=round(confidence, 4),
        replacement=_stable_replacement(category_id, value, masking_salt),
        preview=_preview(value),
        language_hints=language_hints,
        evidence=evidence,
    )


def _dedupe_overlaps(findings: list[PrivacyFinding]) -> list[PrivacyFinding]:
    ordered = sorted(
        findings,
        key=lambda item: (
            item.span_start,
            -(item.span_end - item.span_start),
            -item.confidence,
            item.category_id,
        ),
    )
    accepted: list[PrivacyFinding] = []
    occupied: set[int] = set()
    for item in ordered:
        span = set(range(item.span_start, item.span_end))
        if span & occupied:
            continue
        accepted.append(item)
        occupied.update(span)
    return sorted(accepted, key=lambda item: item.span_start)


def _apply_redactions(text: str, findings: list[PrivacyFinding], *, mode: str) -> str:
    chunks: list[str] = []
    cursor = 0
    for finding in findings:
        chunks.append(text[cursor : finding.span_start])
        original = text[finding.span_start : finding.span_end]
        if mode == "remove":
            replacement = ""
        elif mode == "bracket_label":
            replacement = f"[{finding.category_id}]"
        elif mode == "preserve_shape":
            replacement = _preserve_shape(original)
        else:
            replacement = finding.replacement
        chunks.append(replacement)
        cursor = finding.span_end
    chunks.append(text[cursor:])
    return "".join(chunks)


def _preserve_shape(value: str) -> str:
    output = []
    for char in value:
        if char.isdigit():
            output.append("0")
        elif char.isalpha():
            output.append("x" if char.islower() else "X")
        else:
            output.append(char)
    return "".join(output)


def _stable_replacement(category_id: str, value: str, salt: str) -> str:
    digest = _stable_digest({"category_id": category_id, "value": value, "salt": salt})[:10]
    return f"<privacy:{category_id}:{digest}>"


def _category_summaries(findings: list[PrivacyFinding]) -> list[PrivacyCategorySummary]:
    grouped: dict[str, list[PrivacyFinding]] = {}
    for finding in findings:
        grouped.setdefault(finding.category_id, []).append(finding)
    return [
        PrivacyCategorySummary(
            category_id=category_id,
            label=CATEGORY_BY_ID[category_id].label,
            severity=CATEGORY_BY_ID[category_id].severity,
            count=len(items),
            highest_confidence=round(max(item.confidence for item in items), 4),
        )
        for category_id, items in sorted(grouped.items())
    ]


def _merge_category_summaries(
    summaries: Iterable[PrivacyCategorySummary],
) -> list[PrivacyCategorySummary]:
    grouped: dict[str, list[PrivacyCategorySummary]] = {}
    for summary in summaries:
        grouped.setdefault(summary.category_id, []).append(summary)
    merged: list[PrivacyCategorySummary] = []
    for category_id, items in sorted(grouped.items()):
        spec = CATEGORY_BY_ID[category_id]
        merged.append(
            PrivacyCategorySummary(
                category_id=category_id,
                label=spec.label,
                severity=spec.severity,
                count=sum(item.count for item in items),
                highest_confidence=max(item.highest_confidence for item in items),
            )
        )
    return merged


def _receipt(
    *,
    source_text: str,
    redacted_text: str,
    findings: list[PrivacyFinding],
    masking_mode: str,
    language_hints: list[str],
) -> PrivacyReceipt:
    finding_payload = [
        finding.model_dump(
            mode="json",
            exclude={"preview", "replacement"},
        )
        for finding in findings
    ]
    return PrivacyReceipt(
        source_sha256=_stable_digest(source_text),
        redacted_sha256=_stable_digest(redacted_text),
        finding_set_sha256=_stable_digest(finding_payload),
        detector_version=DETECTOR_VERSION,
        masking_mode=masking_mode,  # type: ignore[arg-type]
        text_length=len(source_text),
        finding_count=len(findings),
        category_count=len({item.category_id for item in findings}),
        language_hints=language_hints,
    )


def _run_record(
    *,
    run_id: str,
    route: str,
    purpose: str,
    tenant_id: str,
    document_count: int,
    responses: list[PrivacyTextResponse],
    notes: list[str],
) -> PrivacyRunRecord:
    category_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    finding_count = 0
    receipts: list[PrivacyReceipt] = []
    for response in responses:
        finding_count += response.finding_count
        receipts.append(response.receipt)
        for summary in response.category_summaries:
            category_counts[summary.category_id] = (
                category_counts.get(summary.category_id, 0) + summary.count
            )
        for language in response.language_hints:
            language_counts[language] = language_counts.get(language, 0) + 1
    return PrivacyRunRecord(
        run_id=run_id,
        route=route,
        purpose=purpose,
        tenant_id=tenant_id,
        document_count=document_count,
        finding_count=finding_count,
        risk_score=round(max((response.risk_score for response in responses), default=0.0), 4),
        highest_severity=_highest_severity(
            finding for response in responses for finding in response.findings
        ),
        category_counts=dict(sorted(category_counts.items())),
        language_counts=dict(sorted(language_counts.items())),
        receipts=receipts,
        persisted_raw_text=False,
        persisted_redacted_text=False,
        notes=[
            *notes,
            "Only receipts and aggregate privacy counts were persisted.",
        ],
    )


def _risk_score(findings: list[PrivacyFinding], text_length: int) -> float:
    if not findings:
        return 0.0
    weighted = sum(SEVERITY_WEIGHT[item.severity] * item.confidence for item in findings)
    density = min(1.0, len(findings) / max(text_length / 800.0, 1.0))
    critical_ratio = sum(1 for item in findings if item.severity == "critical") / len(findings)
    score = min(
        1.0, (weighted / max(len(findings), 1) * 0.52) + (density * 0.28) + (critical_ratio * 0.2)
    )
    return round(score, 4)


def _highest_severity(findings: Iterable[PrivacyFinding]) -> PrivacySeverity:
    rank: dict[PrivacySeverity, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    highest: PrivacySeverity = "low"
    for finding in findings:
        if rank[finding.severity] > rank[highest]:
            highest = finding.severity
    return highest


def _response_notes(findings: list[PrivacyFinding]) -> list[str]:
    notes = [
        (
            "Run this lane before sending support tickets, clinical notes, "
            "transcripts, or claims outside a controlled boundary."
        ),
    ]
    if any(item.detector_kind == "context_label" for item in findings):
        notes.append(
            "Some findings came from explicit labels; review label grammar when forms change."
        )
    if any(
        item.category_id in {"private_key", "bearer_token", "jwt", "api_key"} for item in findings
    ):
        notes.append(
            "Credential-shaped material was present. Rotate the live credential "
            "if this came from a real system."
        )
    if not findings:
        notes.append(
            "No configured high-signal privacy spans were found; this is not "
            "proof that the text is safe."
        )
    return notes


def _language_hints(
    text: str,
    declared: list[str],
    findings: list[PrivacyFinding],
) -> list[str]:
    hints = {item.strip().lower() for item in declared if item.strip()}
    for finding in findings:
        hints.update(item.lower() for item in finding.language_hints)
    if re.search(r"[\u0400-\u04ff]", text):
        hints.add("cyrillic")
    if re.search(r"[\u3040-\u30ff]", text):
        hints.add("japanese")
    if re.search(r"[\u4e00-\u9fff]", text):
        hints.add("chinese")
    if re.search(r"[\uac00-\ud7af]", text):
        hints.add("korean")
    if re.search(r"[\u0600-\u06ff]", text):
        hints.add("arabic")
    if re.search(r"[\u0900-\u097f]", text):
        hints.add("devanagari")
    return sorted(hints)


def _language_hints_for_span(value: str) -> list[str]:
    hints: list[str] = []
    if re.search(r"[\u0400-\u04ff]", value):
        hints.append("cyrillic")
    if re.search(r"[\u3040-\u30ff]", value):
        hints.append("japanese")
    if re.search(r"[\u4e00-\u9fff]", value):
        hints.append("chinese")
    if re.search(r"[\uac00-\ud7af]", value):
        hints.append("korean")
    return hints


def _preview(value: str) -> str:
    stripped = " ".join(value.split())
    if len(stripped) <= 8:
        return "*" * len(stripped)
    return f"{stripped[:2]}...{stripped[-2:]}"


def _context_value_is_useful(value: str) -> bool:
    normalized = value.strip()
    if len(normalized) < 2:
        return False
    if normalized.lower() in {"unknown", "n/a", "none", "redacted"}:
        return False
    return True


def _stable_digest(payload: object) -> str:
    if isinstance(payload, str):
        encoded = payload
    else:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _luhn_valid(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    if len(digits) < 12:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _iban_valid(value: str) -> bool:
    normalized = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", normalized):
        return False
    rotated = normalized[4:] + normalized[:4]
    expanded = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rotated)
    remainder = 0
    for char in expanded:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def _vin_valid(value: str) -> bool:
    normalized = re.sub(r"[^A-HJ-NPR-Z0-9]", "", value.upper())
    return len(normalized) == 17


CATEGORY_SPECS: tuple[CategorySpec, ...] = (
    CategorySpec(
        "person_name",
        "Person name",
        "high",
        "identity",
        "A named person captured through an explicit label.",
        ("context_label",),
        ("multilingual labels",),
    ),
    CategorySpec(
        "email_address",
        "Email address",
        "high",
        "contact",
        "Mailbox or login address.",
        ("pattern",),
    ),
    CategorySpec(
        "phone_number",
        "Phone number",
        "high",
        "contact",
        "International or domestic telephone number.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "street_address",
        "Street address",
        "high",
        "location",
        "Address captured through an explicit label.",
        ("context_label",),
    ),
    CategorySpec(
        "postal_code",
        "Postal code",
        "medium",
        "location",
        "Postal or ZIP code.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "precise_coordinate",
        "Precise coordinate",
        "high",
        "location",
        "Latitude and longitude pair.",
        ("pattern",),
    ),
    CategorySpec(
        "date",
        "Date",
        "medium",
        "temporal",
        "Calendar date that can become identifying in narrow contexts.",
        ("pattern",),
    ),
    CategorySpec(
        "date_of_birth",
        "Date of birth",
        "critical",
        "identity",
        "Birth date captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "age", "Age", "medium", "identity", "Age value captured by label.", ("context_label",)
    ),
    CategorySpec(
        "credit_card",
        "Payment card",
        "critical",
        "financial",
        "Payment card number validated with Luhn checksum.",
        ("checksum",),
    ),
    CategorySpec(
        "iban",
        "IBAN",
        "critical",
        "financial",
        "International bank account number validated with MOD-97.",
        ("checksum",),
    ),
    CategorySpec(
        "bank_routing",
        "Bank routing number",
        "critical",
        "financial",
        "US-style bank routing number.",
        ("pattern",),
    ),
    CategorySpec(
        "bank_account",
        "Bank account",
        "critical",
        "financial",
        "Account number captured through an explicit label.",
        ("context_label",),
    ),
    CategorySpec(
        "swift_bic",
        "SWIFT/BIC",
        "high",
        "financial",
        "International bank routing code.",
        ("pattern",),
    ),
    CategorySpec(
        "crypto_wallet",
        "Crypto wallet",
        "high",
        "financial",
        "Common wallet address format.",
        ("pattern",),
    ),
    CategorySpec(
        "ssn_us",
        "US Social Security number",
        "critical",
        "government",
        "US SSN pattern.",
        ("pattern",),
    ),
    CategorySpec(
        "national_id",
        "National ID",
        "critical",
        "government",
        "Government identifier captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "passport_number",
        "Passport number",
        "critical",
        "government",
        "Passport identifier captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "drivers_license",
        "Driver license",
        "critical",
        "government",
        "Driver license identifier captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "tax_id",
        "Tax ID",
        "critical",
        "government",
        "Taxpayer identifier captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "medical_record_number",
        "Medical record number",
        "critical",
        "healthcare",
        "MRN or patient record number.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "claim_id",
        "Claim ID",
        "high",
        "healthcare",
        "Insurance or benefits claim identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "insurance_member_id",
        "Insurance member ID",
        "critical",
        "healthcare",
        "Health-plan member or subscriber identifier.",
        ("context_label",),
    ),
    CategorySpec(
        "diagnosis_context",
        "Diagnosis context",
        "medium",
        "healthcare",
        "Diagnosis label coupled with personal context.",
        ("context_label",),
    ),
    CategorySpec(
        "genetic_marker",
        "Genetic marker",
        "critical",
        "biometric",
        "Genomic or sequence identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "biometric_reference",
        "Biometric reference",
        "critical",
        "biometric",
        "Face, voice, gait, or fingerprint reference.",
        ("context_label",),
    ),
    CategorySpec(
        "voiceprint_id",
        "Voiceprint ID",
        "critical",
        "biometric",
        "Voiceprint enrollment identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "face_template_id",
        "Face template ID",
        "critical",
        "biometric",
        "Face embedding or template identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "employee_id",
        "Employee ID",
        "high",
        "workforce",
        "Employee identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "student_id",
        "Student ID",
        "high",
        "education",
        "Student or learner identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "case_number",
        "Case number",
        "high",
        "legal",
        "Legal, support, or investigation case number.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "support_ticket",
        "Support ticket",
        "medium",
        "operations",
        "Ticket identifier that can join to a customer record.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "order_id",
        "Order ID",
        "medium",
        "commerce",
        "Order identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "invoice_id",
        "Invoice ID",
        "medium",
        "commerce",
        "Invoice identifier.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "ip_address", "IP address", "high", "network", "IPv4 or IPv6 network address.", ("pattern",)
    ),
    CategorySpec(
        "mac_address", "MAC address", "high", "network", "Hardware network address.", ("pattern",)
    ),
    CategorySpec(
        "device_id",
        "Device ID",
        "high",
        "device",
        "Device identifier captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "imei", "IMEI", "critical", "device", "Mobile device IMEI.", ("pattern", "context_label")
    ),
    CategorySpec(
        "imsi",
        "IMSI",
        "critical",
        "device",
        "Subscriber identity for mobile networks.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "vehicle_vin",
        "Vehicle VIN",
        "high",
        "industrial",
        "Vehicle identification number.",
        ("checksum", "context_label"),
    ),
    CategorySpec(
        "license_plate",
        "License plate",
        "medium",
        "industrial",
        "Vehicle plate captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "asset_serial",
        "Asset serial",
        "medium",
        "industrial",
        "Machine or hardware serial number.",
        ("context_label",),
    ),
    CategorySpec(
        "private_key",
        "Private key",
        "critical",
        "credential",
        "PEM private key block.",
        ("pattern",),
    ),
    CategorySpec(
        "bearer_token",
        "Bearer token",
        "critical",
        "credential",
        "Bearer authorization token.",
        ("pattern",),
    ),
    CategorySpec("jwt", "JWT", "critical", "credential", "JSON Web Token.", ("pattern",)),
    CategorySpec(
        "api_key",
        "API key",
        "critical",
        "credential",
        "API key or cloud access key.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "password",
        "Password",
        "critical",
        "credential",
        "Password captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "session_cookie",
        "Session cookie",
        "critical",
        "credential",
        "Session cookie captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "url_secret",
        "URL secret",
        "critical",
        "credential",
        "URL query string carrying a secret-bearing parameter.",
        ("pattern",),
    ),
    CategorySpec(
        "social_handle",
        "Social handle",
        "medium",
        "online",
        "User handle or account name.",
        ("pattern", "context_label"),
    ),
    CategorySpec(
        "profile_url",
        "Profile URL",
        "medium",
        "online",
        "Social or professional profile URL.",
        ("pattern",),
    ),
    CategorySpec(
        "religion",
        "Religion",
        "high",
        "sensitive_attribute",
        "Religious affiliation captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "political_affiliation",
        "Political affiliation",
        "high",
        "sensitive_attribute",
        "Political affiliation captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "union_membership",
        "Union membership",
        "high",
        "sensitive_attribute",
        "Union affiliation captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "disability_status",
        "Disability status",
        "high",
        "sensitive_attribute",
        "Disability status captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "immigration_status",
        "Immigration status",
        "high",
        "sensitive_attribute",
        "Immigration or visa status captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "caregiver_status",
        "Caregiver status",
        "medium",
        "sensitive_attribute",
        "Caregiving role captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "minor_status",
        "Minor status",
        "critical",
        "sensitive_attribute",
        "Child/minor indicator captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "household_income",
        "Household income",
        "medium",
        "sensitive_attribute",
        "Income captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "precise_school",
        "Precise school",
        "medium",
        "education",
        "School identity captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "worksite_location",
        "Worksite location",
        "medium",
        "workforce",
        "Specific worksite captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "emergency_contact",
        "Emergency contact",
        "critical",
        "contact",
        "Emergency contact captured by label.",
        ("context_label",),
    ),
    CategorySpec(
        "next_of_kin",
        "Next of kin",
        "critical",
        "contact",
        "Next-of-kin captured by label.",
        ("context_label",),
    ),
)

CATEGORY_BY_ID = {item.category_id: item for item in CATEGORY_SPECS}


DETECTOR_RULES: tuple[DetectorRule, ...] = (
    DetectorRule(
        "email_address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
        0.98,
        "pattern",
        "email address grammar",
    ),
    DetectorRule(
        "phone_number",
        re.compile(
            r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?!\w)"
        ),
        0.72,
        "pattern",
        "telephone-like digit grouping",
    ),
    DetectorRule(
        "credit_card",
        re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"),
        0.96,
        "checksum",
        "Luhn-valid payment card number",
        _luhn_valid,
    ),
    DetectorRule(
        "iban",
        re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b", re.I),
        0.97,
        "checksum",
        "MOD-97-valid IBAN",
        _iban_valid,
    ),
    DetectorRule(
        "swift_bic",
        re.compile(r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
        0.72,
        "pattern",
        "SWIFT/BIC grammar",
    ),
    DetectorRule(
        "ssn_us",
        re.compile(r"\b(?!000|666|9\d\d)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"),
        0.93,
        "pattern",
        "US SSN grammar",
    ),
    DetectorRule(
        "bank_routing", re.compile(r"\b\d{9}\b"), 0.62, "pattern", "nine digit routing-like number"
    ),
    DetectorRule(
        "medical_record_number",
        re.compile(r"\b(?:MRN|MedRec|Patient ID)[:#\s-]*[A-Z0-9-]{5,24}\b", re.I),
        0.92,
        "pattern",
        "medical-record label plus identifier",
    ),
    DetectorRule(
        "claim_id",
        re.compile(r"\b(?:claim|claim id|case claim)[:#\s-]*[A-Z0-9-]{6,28}\b", re.I),
        0.82,
        "pattern",
        "claim label plus identifier",
    ),
    DetectorRule(
        "employee_id",
        re.compile(r"\b(?:EMP|Employee)[:#\s-]*[A-Z0-9-]{4,20}\b", re.I),
        0.8,
        "pattern",
        "employee label plus identifier",
    ),
    DetectorRule(
        "student_id",
        re.compile(r"\b(?:STU|Student)[:#\s-]*[A-Z0-9-]{4,20}\b", re.I),
        0.8,
        "pattern",
        "student label plus identifier",
    ),
    DetectorRule(
        "case_number",
        re.compile(r"\b(?:case|matter)[:#\s-]*[A-Z]{0,4}\d[A-Z0-9-]{5,28}\b", re.I),
        0.78,
        "pattern",
        "case label plus identifier",
    ),
    DetectorRule(
        "support_ticket",
        re.compile(r"\b(?:ticket|support)[:#\s-]*(?:TKT|SUP)?[A-Z0-9-]{5,24}\b", re.I),
        0.74,
        "pattern",
        "support ticket label plus identifier",
    ),
    DetectorRule(
        "order_id",
        re.compile(r"\b(?:order|purchase)[:#\s-]*(?:ORD)?[A-Z0-9-]{5,24}\b", re.I),
        0.68,
        "pattern",
        "order label plus identifier",
    ),
    DetectorRule(
        "invoice_id",
        re.compile(r"\b(?:invoice|inv)[:#\s-]*(?:INV)?[A-Z0-9-]{5,24}\b", re.I),
        0.68,
        "pattern",
        "invoice label plus identifier",
    ),
    DetectorRule(
        "ip_address",
        re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
        0.91,
        "pattern",
        "IPv4 grammar",
    ),
    DetectorRule(
        "ip_address",
        re.compile(r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b", re.I),
        0.86,
        "pattern",
        "IPv6 grammar",
    ),
    DetectorRule(
        "mac_address",
        re.compile(r"\b(?:[A-F0-9]{2}[:-]){5}[A-F0-9]{2}\b", re.I),
        0.9,
        "pattern",
        "MAC address grammar",
    ),
    DetectorRule("imei", re.compile(r"\b\d{15}\b"), 0.68, "pattern", "15 digit IMEI-like value"),
    DetectorRule(
        "imsi", re.compile(r"\b\d{14,15}\b"), 0.58, "pattern", "14-15 digit IMSI-like value"
    ),
    DetectorRule(
        "vehicle_vin",
        re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"),
        0.86,
        "checksum",
        "VIN grammar without I/O/Q",
        _vin_valid,
    ),
    DetectorRule(
        "private_key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"),
        0.99,
        "pattern",
        "PEM private key block",
    ),
    DetectorRule(
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b"),
        0.97,
        "pattern",
        "Bearer authorization token",
    ),
    DetectorRule(
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        0.98,
        "pattern",
        "JWT compact serialization",
    ),
    DetectorRule(
        "api_key",
        re.compile(r"\b(?:sk|pk|api|key|token)[_-]?(?:live|test)?[_-]?[A-Za-z0-9]{20,}\b", re.I),
        0.86,
        "pattern",
        "API key-like token",
    ),
    DetectorRule(
        "api_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0.98, "pattern", "AWS access key id"
    ),
    DetectorRule(
        "url_secret",
        re.compile(r"https?://[^\s]+[?&](?:token|key|secret|signature|code|auth)=[^\s&#]+", re.I),
        0.94,
        "pattern",
        "URL query contains secret-bearing parameter",
    ),
    DetectorRule(
        "crypto_wallet",
        re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
        0.9,
        "pattern",
        "Ethereum wallet grammar",
    ),
    DetectorRule(
        "crypto_wallet",
        re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
        0.78,
        "pattern",
        "Bitcoin wallet grammar",
    ),
    DetectorRule(
        "precise_coordinate",
        re.compile(
            r"(?<!\d)-?(?:[1-8]?\d(?:\.\d+)?|90(?:\.0+)?),\s*-?(?:1[0-7]\d(?:\.\d+)?|[1-9]?\d(?:\.\d+)?|180(?:\.0+)?)(?!\d)"
        ),
        0.88,
        "pattern",
        "latitude and longitude pair",
    ),
    DetectorRule(
        "date",
        re.compile(r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b"),
        0.58,
        "pattern",
        "calendar date grammar",
    ),
    DetectorRule(
        "profile_url",
        re.compile(
            r"https?://(?:www\.)?(?:linkedin|facebook|instagram|x|twitter|github)\.com/[A-Za-z0-9_./-]+",
            re.I,
        ),
        0.78,
        "pattern",
        "social or professional profile URL",
    ),
    DetectorRule(
        "social_handle",
        re.compile(r"(?<![\w.])@[A-Za-z0-9_]{3,32}\b"),
        0.64,
        "pattern",
        "public handle grammar",
    ),
    DetectorRule(
        "voiceprint_id",
        re.compile(r"\bvoice(?:print)?[_-]?(?:id|template)[:#\s-]*[A-Z0-9-]{6,32}\b", re.I),
        0.92,
        "pattern",
        "voiceprint identifier",
    ),
    DetectorRule(
        "face_template_id",
        re.compile(r"\bface[_-]?(?:id|template|embedding)[:#\s-]*[A-Z0-9-]{6,32}\b", re.I),
        0.92,
        "pattern",
        "face template identifier",
    ),
    DetectorRule(
        "genetic_marker",
        re.compile(r"\b(?:rs\d{3,12}|chr(?:[1-9]|1\d|2[0-2]|X|Y):\d{2,12})\b", re.I),
        0.86,
        "pattern",
        "genetic marker notation",
    ),
)


CONTEXT_LABELS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("name", "person_name", ("english",)),
    ("full name", "person_name", ("english",)),
    ("pangalan", "person_name", ("filipino",)),
    ("nombre", "person_name", ("spanish",)),
    ("nom", "person_name", ("french",)),
    ("nome", "person_name", ("italian", "portuguese")),
    ("naam", "person_name", ("dutch",)),
    ("imya", "person_name", ("russian",)),
    ("namae", "person_name", ("japanese",)),
    ("ireum", "person_name", ("korean",)),
    ("address", "street_address", ("english",)),
    ("direccion", "street_address", ("spanish",)),
    ("adresse", "street_address", ("french", "german")),
    ("tirahan", "street_address", ("filipino",)),
    ("dob", "date_of_birth", ("english",)),
    ("date of birth", "date_of_birth", ("english",)),
    ("birthdate", "date_of_birth", ("english",)),
    ("edad", "age", ("spanish",)),
    ("age", "age", ("english",)),
    ("phone", "phone_number", ("english",)),
    ("telefono", "phone_number", ("spanish", "italian")),
    ("mobile", "phone_number", ("english",)),
    ("postal code", "postal_code", ("english",)),
    ("zip", "postal_code", ("english",)),
    ("account", "bank_account", ("english",)),
    ("bank account", "bank_account", ("english",)),
    ("national id", "national_id", ("english",)),
    ("passport", "passport_number", ("english",)),
    ("driver license", "drivers_license", ("english",)),
    ("tax id", "tax_id", ("english",)),
    ("mrn", "medical_record_number", ("english",)),
    ("patient id", "medical_record_number", ("english",)),
    ("member id", "insurance_member_id", ("english",)),
    ("insurance id", "insurance_member_id", ("english",)),
    ("diagnosis", "diagnosis_context", ("english",)),
    ("genetic marker", "genetic_marker", ("english",)),
    ("biometric", "biometric_reference", ("english",)),
    ("voiceprint", "voiceprint_id", ("english",)),
    ("face template", "face_template_id", ("english",)),
    ("employee id", "employee_id", ("english",)),
    ("student id", "student_id", ("english",)),
    ("case", "case_number", ("english",)),
    ("ticket", "support_ticket", ("english",)),
    ("order", "order_id", ("english",)),
    ("invoice", "invoice_id", ("english",)),
    ("device id", "device_id", ("english",)),
    ("imei", "imei", ("english",)),
    ("imsi", "imsi", ("english",)),
    ("vin", "vehicle_vin", ("english",)),
    ("plate", "license_plate", ("english",)),
    ("serial", "asset_serial", ("english",)),
    ("api key", "api_key", ("english",)),
    ("password", "password", ("english",)),
    ("session", "session_cookie", ("english",)),
    ("handle", "social_handle", ("english",)),
    ("religion", "religion", ("english",)),
    ("political affiliation", "political_affiliation", ("english",)),
    ("union", "union_membership", ("english",)),
    ("disability", "disability_status", ("english",)),
    ("immigration status", "immigration_status", ("english",)),
    ("visa status", "immigration_status", ("english",)),
    ("caregiver", "caregiver_status", ("english",)),
    ("minor", "minor_status", ("english",)),
    ("household income", "household_income", ("english",)),
    ("school", "precise_school", ("english",)),
    ("worksite", "worksite_location", ("english",)),
    ("emergency contact", "emergency_contact", ("english",)),
    ("next of kin", "next_of_kin", ("english",)),
)
