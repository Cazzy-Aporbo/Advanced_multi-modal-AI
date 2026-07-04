# Privacy Membrane

- Detector version: `privacy-membrane-2026.07`
- Categories: `63`
- Language hints: `20`
- Deterministic category coverage: `101`
- Sample source hash: `9bd10dbad21a44770ff9d3c19edfcf9c6b98e7752d130595547b02808595fa25`
- Sample redacted hash: `2a19669fc54fd0ee35c684f74972c91bbab7462dcb70440b51e99211f44a7d6a`
- Sample finding-set hash: `e9252e999b089fcd24b3e42692de8725d45ac3351e26d142e63655b4262d9b3a`

## Boundary notes

- This lane performs local deterministic detection and masking. It does not claim trained-token classification.
- The recognizers favor high-signal evidence: checksums, explicit labels, keyed secrets, and structured identifiers.
- Broad person-name and street-address recognition is limited to context labels to avoid pretending that general NER is present.
- The store persists receipts and aggregate counts only; raw text and redacted text are returned to the caller but not saved.

## Sample finding summary

- `credit_card` · 1 finding(s) · confidence 0.96
- `date_of_birth` · 1 finding(s) · confidence 0.82
- `email_address` · 1 finding(s) · confidence 0.98
- `medical_record_number` · 1 finding(s) · confidence 0.92
- `person_name` · 1 finding(s) · confidence 0.82

## Category register excerpt

- `person_name` · high · context_label
- `email_address` · high · pattern
- `phone_number` · high · pattern, context_label
- `street_address` · high · context_label
- `postal_code` · medium · pattern, context_label
- `precise_coordinate` · high · pattern
- `date` · medium · pattern
- `date_of_birth` · critical · context_label
- `age` · medium · context_label
- `credit_card` · critical · checksum
- `iban` · critical · checksum
- `bank_routing` · critical · pattern
- `bank_account` · critical · context_label
- `swift_bic` · high · pattern
- `crypto_wallet` · high · pattern
- `ssn_us` · critical · pattern
- `national_id` · critical · context_label
- `passport_number` · critical · context_label
- `drivers_license` · critical · context_label
- `tax_id` · critical · context_label
- `medical_record_number` · critical · pattern, context_label
- `claim_id` · high · pattern, context_label
- `insurance_member_id` · critical · context_label
- `diagnosis_context` · medium · context_label
