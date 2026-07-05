# Privacy Membrane

- Detector version: `privacy-membrane-2026.07`
- Categories: `63`
- Language hints: `32`
- Deterministic category coverage: `133`
- Family counts: `{'biometric': 4, 'commerce': 2, 'contact': 4, 'credential': 7, 'device': 3, 'education': 2, 'financial': 6, 'government': 5, 'healthcare': 4, 'identity': 3, 'industrial': 3, 'legal': 1, 'location': 3, 'network': 2, 'online': 2, 'operations': 1, 'sensitive_attribute': 8, 'temporal': 1, 'workforce': 2}`
- Severity counts: `{'critical': 28, 'high': 20, 'medium': 15}`
- Sample source hash: `9bd10dbad21a44770ff9d3c19edfcf9c6b98e7752d130595547b02808595fa25`
- Sample redacted hash: `2a19669fc54fd0ee35c684f74972c91bbab7462dcb70440b51e99211f44a7d6a`
- Sample finding-set hash: `e9252e999b089fcd24b3e42692de8725d45ac3351e26d142e63655b4262d9b3a`

## Boundary notes

- This lane performs local deterministic detection and masking. It does not claim trained-token classification.
- The recognizers favor high-signal evidence: checksums, explicit labels, keyed secrets, and structured identifiers.
- Broad person-name and street-address recognition is limited to context labels to avoid pretending that general NER is present.
- The store persists receipts and aggregate counts only; raw text and redacted text are returned to the caller but not saved.

## Design principles

- `minimize-first` · Keep the working set small: The detector returns redacted text to the caller and persists receipts, counts, and hashes rather than raw documents.
- `purpose-bound` · Carry a stated purpose: Every privacy run carries a purpose and tenant lane so review can ask why the text was processed, not only whether a pattern matched.
- `local-before-network` · Inspect locally before transfer: The membrane is deterministic Python code that can run before support, clinical, or claims text leaves a controlled process.
- `receipt-without-replay` · Prove without repeating: Receipts hash the source, redacted output, and finding set so a run can be checked later without storing the sensitive words.
- `rotate-live-secrets` · Treat exposed credentials as active incidents: Credential-shaped findings produce response notes that recommend rotation when the sample came from a real system.

## Source anchors

- `gdpr-art-5`: [GDPR Article 5: principles relating to processing of personal data](https://gdpr-info.eu/art-5-gdpr/) (Intersoft Consulting GDPR reference). Used for minimization, purpose limitation, accuracy, storage limitation, and integrity language.
- `gdpr-art-25`: [GDPR Article 25: data protection by design and by default](https://gdpr-info.eu/art-25-gdpr/) (Intersoft Consulting GDPR reference). Used for privacy-by-design and default narrowing posture.
- `ccpa-cpra-rights`: [California Consumer Privacy Act guidance](https://oag.ca.gov/privacy/ccpa) (California Department of Justice). Used for access, deletion, correction, opt-out, and sensitive personal information awareness.
- `nist-privacy-framework`: [NIST Privacy Framework](https://www.nist.gov/privacy-framework) (National Institute of Standards and Technology). Used for privacy risk, governance, communication, and control mapping language.
- `hoepman-privacy-design`: [Privacy Design Strategies](https://www.cs.ru.nl/~jhh/publications/pdp.pdf) (Jaap-Henk Hoepman). Used for minimize, hide, separate, aggregate, inform, control, enforce, and demonstrate strategies.
- `owasp-secrets-management`: [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) (OWASP Cheat Sheet Series). Used for credential rotation and secret-handling notes.

## Sample finding summary

- `credit_card` · 1 finding(s) · confidence 0.96
- `date_of_birth` · 1 finding(s) · confidence 0.82
- `email_address` · 1 finding(s) · confidence 0.98
- `medical_record_number` · 1 finding(s) · confidence 0.92
- `person_name` · 1 finding(s) · confidence 0.82

## Category register

| Category | Family | Severity | Detector kinds | Why it matters |
| --- | --- | --- | --- | --- |

| `person_name` | identity | high | context_label | Identity traces make separate records joinable. A harmless note can become personal when it is paired with a date, location, or case detail. |
| `email_address` | contact | high | pattern | Contact fields create direct reachability and can expose families or caretaking relationships. |
| `phone_number` | contact | high | pattern, context_label | Contact fields create direct reachability and can expose families or caretaking relationships. |
| `street_address` | location | high | context_label | Precise place can reveal home, school, clinic, worksite, or travel patterns. |
| `postal_code` | location | medium | pattern, context_label | Precise place can reveal home, school, clinic, worksite, or travel patterns. |
| `precise_coordinate` | location | high | pattern | Precise place can reveal home, school, clinic, worksite, or travel patterns. |
| `date` | temporal | medium | pattern | Dates become identifying when they describe a rare event, birth record, accident, or narrow cohort. |
| `date_of_birth` | identity | critical | context_label | Identity traces make separate records joinable. A harmless note can become personal when it is paired with a date, location, or case detail. |
| `age` | identity | medium | context_label | Identity traces make separate records joinable. A harmless note can become personal when it is paired with a date, location, or case detail. |
| `credit_card` | financial | critical | checksum | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `iban` | financial | critical | checksum | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `bank_routing` | financial | critical | pattern | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `bank_account` | financial | critical | context_label | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `swift_bic` | financial | high | pattern | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `crypto_wallet` | financial | high | pattern | Financial identifiers can enable fraud, account takeover, or unintended payment linkage. |
| `ssn_us` | government | critical | pattern | Government identifiers are durable. Once copied widely, they are difficult for a person to change. |
| `national_id` | government | critical | context_label | Government identifiers are durable. Once copied widely, they are difficult for a person to change. |
| `passport_number` | government | critical | context_label | Government identifiers are durable. Once copied widely, they are difficult for a person to change. |
| `drivers_license` | government | critical | context_label | Government identifiers are durable. Once copied widely, they are difficult for a person to change. |
| `tax_id` | government | critical | context_label | Government identifiers are durable. Once copied widely, they are difficult for a person to change. |
| `medical_record_number` | healthcare | critical | pattern, context_label | Health context can affect dignity, employment, insurance, and family privacy. |
| `claim_id` | healthcare | high | pattern, context_label | Health context can affect dignity, employment, insurance, and family privacy. |
| `insurance_member_id` | healthcare | critical | context_label | Health context can affect dignity, employment, insurance, and family privacy. |
| `diagnosis_context` | healthcare | medium | context_label | A diagnosis can become identifying when paired with timing, geography, employer, or rare symptoms. |
| `genetic_marker` | biometric | critical | pattern, context_label | Biometric traces are intimate and hard to replace. They can identify a person even when names are absent. |
| `biometric_reference` | biometric | critical | context_label | Biometric traces are intimate and hard to replace. They can identify a person even when names are absent. |
| `voiceprint_id` | biometric | critical | pattern, context_label | Biometric traces are intimate and hard to replace. They can identify a person even when names are absent. |
| `face_template_id` | biometric | critical | pattern, context_label | Biometric traces are intimate and hard to replace. They can identify a person even when names are absent. |
| `employee_id` | workforce | high | pattern, context_label | Work records can expose performance, discipline, location, and economic vulnerability. |
| `student_id` | education | high | pattern, context_label | Education records often concern minors or young adults and can follow people for years. |
| `case_number` | legal | high | pattern, context_label | A case number can unlock a sensitive story even when the surrounding text is modest. |
| `support_ticket` | operations | medium | pattern, context_label | Operational tickets often mix identity, account state, secrets, and emotional context in one place. |
| `order_id` | commerce | medium | pattern, context_label | Commerce IDs can connect a person to purchase habits, household needs, or location. |
| `invoice_id` | commerce | medium | pattern, context_label | Commerce IDs can connect a person to purchase habits, household needs, or location. |
| `ip_address` | network | high | pattern | Network identifiers can become personal when tied to accounts, locations, or device history. |
| `mac_address` | network | high | pattern | Network identifiers can become personal when tied to accounts, locations, or device history. |
| `device_id` | device | high | context_label | Device identifiers can track a person across apps, homes, networks, and time. |
| `imei` | device | critical | pattern, context_label | Device identifiers can track a person across apps, homes, networks, and time. |
| `imsi` | device | critical | pattern, context_label | Device identifiers can track a person across apps, homes, networks, and time. |
| `vehicle_vin` | industrial | high | checksum, context_label | Machine IDs can reveal owner, site, operator, and business activity. |
| `license_plate` | industrial | medium | context_label | Machine IDs can reveal owner, site, operator, and business activity. |
| `asset_serial` | industrial | medium | context_label | Machine IDs can reveal owner, site, operator, and business activity. |
| `private_key` | credential | critical | pattern | A secret is not only private; it may still be live authority. |
| `bearer_token` | credential | critical | pattern | A secret is not only private; it may still be live authority. |
| `jwt` | credential | critical | pattern | A secret is not only private; it may still be live authority. |
| `api_key` | credential | critical | pattern, context_label | A secret is not only private; it may still be live authority. |
| `password` | credential | critical | context_label | A secret is not only private; it may still be live authority. |
| `session_cookie` | credential | critical | context_label | A secret is not only private; it may still be live authority. |
| `url_secret` | credential | critical | pattern | A link can carry authority inside the query string, even when the visible page looks ordinary. |
| `social_handle` | online | medium | pattern, context_label | Online handles can reconnect a private workstream to a public life. |
| `profile_url` | online | medium | pattern | Online handles can reconnect a private workstream to a public life. |
| `religion` | sensitive_attribute | high | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `political_affiliation` | sensitive_attribute | high | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `union_membership` | sensitive_attribute | high | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `disability_status` | sensitive_attribute | high | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `immigration_status` | sensitive_attribute | high | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `caregiver_status` | sensitive_attribute | medium | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `minor_status` | sensitive_attribute | critical | context_label | A child indicator changes the duty of care. It should make review slower, not more theatrical. |
| `household_income` | sensitive_attribute | medium | context_label | Sensitive attributes can create unfair treatment even when no name is present. |
| `precise_school` | education | medium | context_label | Education records often concern minors or young adults and can follow people for years. |
| `worksite_location` | workforce | medium | context_label | Work records can expose performance, discipline, location, and economic vulnerability. |
| `emergency_contact` | contact | critical | context_label | This field describes another person who may not be the primary user and may not know the record exists. |
| `next_of_kin` | contact | critical | context_label | Kinship data can expose family structure, dependency, and grief context. |
