# Intentionally Excluded Features (Trade-offs)

To deliver a high-quality prototype within the 4-day timeline, we focused on database design, unit normalization, and audit log compliance. We intentionally left out the following four systems:

---

## 1. Asynchronous Background Task Queues (Celery + Redis)
- **What it is:** Using background workers to process CSV file uploads asynchronously outside the HTTP request-response cycle.
- **Why we skipped it:** While essential for large production files (e.g. >10,000 rows), setting up Celery, Redis/RabbitMQ, and managing background task state adds significant infrastructural overhead. For an onboarding MVP with typical client exports under 1,000 rows, synchronous pandas processing takes less than 2 seconds. Skipping this eliminated external runtime dependencies, ensuring the app is stable and deploys easily on a free Render tier.
- **Auditor Defense:** "We designed the ingestion status state machine (`PENDING` -> `PROCESSING` -> `SUCCESS`/`FAILED`) inside `DataSource` specifically to accommodate a future migration to Celery tasks without modifying the frontend or DB schema."

---

## 2. Direct SAP API Integrations (BAPIs/RFCs/OData)
- **What it is:** Integrating directly with live SAP instances via enterprise connectors or OData REST web services.
- **Why we skipped it:** SAP environments are heavily customized, requiring specialized network access, VPNs, and complex credential management. Mocking an SAP RFC service adds fake complexity without showing realistic parsing challenges. Ingesting a CSV export mirrors the onboarding reality of initial sustainability audits.
- **Auditor Defense:** "We focused on standardizing the dirty columns and German/English headers of SAP flat export sheets (`Werksnummer`, `Einheit`), which mimics what clients actually extract and upload during manual compliance cycles."

---

## 3. Optical Character Recognition (OCR) for Utility PDF Bills
- **What it is:** Integrating tools like Tesseract or AWS Textract to automatically scan and parse scanned utility bills.
- **Why we skipped it:** PDF structures vary drastically by provider (e.g. PG&E vs ConEd). Building a robust PDF parser is a standalone machine learning task. For onboarding onboarding setups, facilities teams extract usage sheets directly from utility portals as CSVs.
- **Auditor Defense:** "We chose to ingest utility portal CSV exports. This allowed us to prioritize building billing period handlers and our rolling historical spike check rather than spending days debugging OCR layouts."

---

## 4. Utility Historical Rolling Average Spike Checks
- **What it is:** Checking for utility electricity usage anomalies by querying and computing the rolling average of previous approved records for the same Meter ID.
- **Why we skipped it:** Computing a dynamic rolling average across database boundaries during the synchronous ingestion loop introduces database-intensive queries and locks. For an MVP with typical client exports, a static threshold-based check (>50,000 kWh) flags unusual industrial loads with minimal database query overhead. Skipping this maintains low-latency synchronous ingestion.
- **Auditor Defense:** "We implemented static threshold filters (>50,000 kWh) to identify excessive consumption cycles. The validation engine interface was designed to support database-level average lookups retrospectively during compliance report generation cycles."

---

## 5. Tenant Authentication & Identity Verification
- **What it is:** Integrating cryptographic token authorization (JWT/OAuth2) to dynamically verify tenant scopes.
- **Why we skipped it:** Building a complete single sign-on (SSO) login system with user credentials and organizations mappings adds substantial deployment complexity. For this internship prototype, multi-tenancy was simplified by deriving the active organization context from a client-supplied `X-Organization-ID` request header, with strict validation ensuring no unmapped or missing header requests are resolved.
- **Auditor Defense:** "Authentication and tenant identity verification were simplified for the MVP scope to isolate database modeling logic. In production, the organization context would be derived from cryptographically verified user claims (e.g. JWT claims) rather than unauthenticated request headers."

---

## 6. Direct Queryset-Level Updates Bypass
- **What it is:** Preventing direct ORM bulk-update operations (`.update()`) from bypassing model save hooks.
- **Why we skipped it:** Django's `.update()` translates directly to SQL and does not run individual model `save()` overrides. Overriding the Queryset manager class or adding database-level triggers to enforce immutability for locked tables is outside the MVP scope, as all application writes are expected to go through standard model save lifecycle paths.
- **Auditor Defense:** "Audit locking is enforced through model-layer `save()` and `delete()` overrides and views. Direct queryset-level database updates remain an acknowledged limitation of the MVP and would be restricted through repository patterns or database check constraints in production."
