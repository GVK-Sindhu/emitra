# Architectural & Ingestion Decisions

This document details the engineering decisions made for the ESG Ingestion Platform prototype.

---

## 1. Why CSV Ingestion was Chosen
- **Real-World Relevance:** Despite having advanced APIs, enterprise data onboarding almost always begins with CSV/Excel dumps extracted from corporate networks (SAP, Utility portals, Concur expense portals).
- **Format Flexibility:** CSV allows us to write custom cleaning pipelines using `pandas` to demonstrate how we parse dirty, unstructured raw strings before inserting them into a normalized PostgreSQL schema.
- **Low Overhead:** Avoids heavy API authentication setups and vendor sandbox needs for mock endpoints.

---

## 2. Ingestion & Normalization Assumptions

### SAP ERP Ingestion
- **Headers:** Assumed headers can be in English or German (e.g. `Menge` / `Fuel Quantity`). The system maps common German labels to English labels before row initialization.
- **Unit Standardization:** Supported units include Gallons, Liters (L), and cubic meters (m3). The system standardizes liquid volume to Liters (`L`) and gases to cubic meters (`m3`).
- **Dates:** Supported formats are standard ISO (`YYYY-MM-DD`) and European dot notation (`DD.MM.YYYY`).

### Utility Ingestion
- **Grid Electricity Focus:** Normalized usage goes to kilowatt-hours (`kWh`).
- **Billing Periods:** Real utility billing cycles span mid-month (e.g., April 15 to May 14). The model stores billing period start/end and maps the emissions to the posting period.
- **Threshold-Based Spike Check:** Historical rolling average checks have been deferred for the MVP scope to reduce database-intensive queries during ingestion. Instead, a static threshold-based anomaly detection is implemented. Any utility billing record exceeding 50,000 kWh of energy consumption is automatically flagged as suspicious.

### Business Travel Ingestion
- **Missing Distance Estimation:** Distance is often omitted in Concur/Navan logs. If airport IATA codes (`From Airport`, `To Airport`) are present, we look up coordinates and calculate miles using the **Haversine formula**.
- **Ground transport Estimation:** If ground transportation is text like "Taxi", the system assumes a standard trip distance of 15 miles. If "Train", it assumes 30 miles. If it's numeric, the system reads it as passenger-miles directly.

---

## 3. Key Product Tradeoffs
- **Synchronous Ingestion:** Large CSVs (>100k rows) should be handled via Celery/Redis. For this prototype MVP, ingestion is run synchronously inside the API thread. This ensures zero infrastructural deployment complexity on Render while keeping onboarding responsive for typical client files (100–500 rows).
- **Simplified Tenant Mapping:** We identify organization context via an HTTP header (`X-Organization-ID`) rather than building full single sign-on (SSO) login systems, focusing on data model isolation.

---

## 4. Product Manager Questions
1. *How should we handle billing period splitting for utility cycles crossing calendar years? (e.g., December 15 to January 14). Do we split the emissions proportionally by day or assign the emissions to the billing start month?*
2. *Should we allow administrators to override standard emission factors? Currently, analysts can edit emission factors directly, but should factor sets be restricted to corporate-approved catalogs?*
3. *What is the SLA for suspicious records? Do we block the final report submission if there are pending suspicious flags, or are flags purely advisory for auditors?*
4. *Do we need support for Scope 3 employee commute data in the next phase, or is corporate travel the only category we are auditing?*

---

## 5. Tenant Isolation & Security
- **Organization Filtering**: To prevent tenant enumeration and data spoofing, `OrganizationViewSet` overrides `get_queryset()` to filter query results dynamically using the resolved active organization context (`X-Organization-ID` header).
- **Security Scope**: Anonymous queries listing all tenants are blocked, and requests attempting to retrieve other tenant details directly return an HTTP `404 Not Found` response.
