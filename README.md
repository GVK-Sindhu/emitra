# Emitra ESG Data Pipeline

Emitra is a prototype platform designed for greenhouse gas (GHG) emissions data ingestion, automated unit normalization, and analyst review workflows. Developed as a Django REST and React application, it provides sustainability analysts with tools to upload utility, travel, and procurement exports, resolve anomalies, approve entries for compliance, and maintain a queryable audit trail. The system isolates data per tenant using request headers to simulate multi-tenant boundaries.

## Live Demo

- **Frontend URL**: [https://emitra-two.vercel.app](https://emitra-two.vercel.app)
- **Backend URL**: [https://emitra-backend-lpg5.onrender.com/api/](https://emitra-backend-lpg5.onrender.com/api/)
- **Demo User**: `analyst@acme.com`

## Assignment Scope

In sustainability audits, data originates from mismatched source formats (e.g. German SAP exports, utility portal sheets, travel agency logs) and requires consolidation. Analysts must convert varied physical quantities (e.g. gallons, liters, MWh) into standardized units, calculate metric tons of CO2 equivalent (tCO2e), flag calculation errors or unrealistic entries, and maintain an immutable record after auditing. Emitra addresses this by automating CSV data parsing, calculation schema execution, anomaly detection, and providing review and log screens.

## Architecture

```
                       React Frontend (Vercel)
                                  ↓ 
                        [X-Organization-ID]
                                  ↓ 
                       Django REST API (Render)
                                  ↓ 
                        Neon PostgreSQL DB
```

- **Frontend**: Single Page Application built using React, Vite, and Lucide React, styled in clean light-mode CSS.
- **Backend**: Django REST Framework API routing database ingestion, schema serialization, validation rules, and audit logs.
- **Database**: Managed PostgreSQL instance hosted on Neon.

## Supported Data Sources

The platform processes three realistic enterprise data sources:
1. **SAP ERP (Fuel / Procurement)**: Ingests direct scope 1 fuel data. Automatically handles German/English header mapping (e.g. `Menge` to `Fuel Quantity`, `Einheit` to `Fuel Unit`) and normalizes liquid volumes to Liters (`L`) or natural gas to cubic meters (`m3`).
2. **Utility Portal (Electricity)**: Ingests scope 2 indirect emissions. Captures Billing Start and End cycles, meter IDs, and converts electricity units (e.g. MWh, Wh) to kilowatt-hours (`kWh`).
3. **Corporate Travel (Navan/Concur API)**: Ingests scope 3 value-chain business travel. Handles flight segments (calculating distance from IATA codes using the Haversine formula if missing), hotel night stays, and ground transportation.

## Core Features

- **Multi-Tenant Partitioning**: Isolates all database queries and updates by validating the incoming `X-Organization-ID` HTTP header.
- **Synchronous Normalization Pipeline**: Processes uploaded CSV files row-by-row, converts physical units, and calculates `tCO2e` emissions using standardized factor tables.
- **Automated Validation Engine**: Flags negative quantities, excessive usages (e.g., >50k kWh electricity), missing airport codes, and cancelled travel records.
- **Analyst Approval Workflow**: Allows reviewing flagged records, locking approved records from future writes, and capturing mandatory analyst reason codes.
- **Compliance Audit Log**: Records pre-update and post-update JSON deltas whenever an analyst modifies a record.

## Data Model Overview

The database utilizes five relational tables to ensure data integrity:
- **`Organization`**: Represents the tenant entity (e.g. "Acme Corporation") partitioning the platform's data.
- **`DataSource`**: Tracks uploaded CSV files, their source types, upload times, and ingestion status.
- **`RawRecord`**: Stores the exact, unprocessed JSON dictionary of each CSV row, preserving the raw source of truth for potential future calculations.
- **`EmissionRecord`**: Holds normalized activity data (normalized quantities/units), calculated `tCO2e` values, suspicious flags, and audit lock flags.
- **`AuditLog`**: Stores immutable historical logs of analyst edits, preserving the user info, timestamp, change reason, and the pre/post state changes.

For the full entity-relationship diagram and detailed table schemas, refer to [MODEL.md](file:///d:/projects/Emitra/MODEL.md).

## Analyst Workflow

```
[CSV Upload] ➔ [Row-by-Row Ingestion] ➔ [Validation Check] ➔ [Analyst Review] ➔ [Approval/Update] ➔ [Record Locked]
```
1. **Ingest**: The analyst selects a source type (SAP, Utility, or Travel) and uploads a CSV file.
2. **Normalize**: The backend parses rows, saves the raw state, converts units (e.g., MWh -> kWh), and calculates tCO2e.
3. **Flag**: Validation rules assess records. If crucial data is missing, the row is marked as `FAILED`. If a threshold is crossed, the record is flagged as `SUSPICIOUS` but saved.
4. **Audit & Lock**: The analyst reviews the dashboard. If edits are made, the analyst must provide a reason, generating an `AuditLog` entry. Once approved, the record is locked (`locked_for_audit = True`), preventing any further updates or deletions.

## Suspicious Record Detection

The pipeline applies static rules to flag anomalous values:
- **Negative Values**: Flags negative values in quantity fields (e.g. negative electricity usage).
- **Extreme Thresholds**: Flags fuel purchases exceeding 100,000 Liters or electricity usage exceeding 50,000 kWh in a billing period.
- **Invalid Airport Codes**: Flags travel entries containing unrecognized IATA source/destination codes (e.g. non-standard IATA codes).
- **Cancelled Trips**: Identifies cancelled or voided flight segments, normalizing their emissions to `0 tCO2e` and flagging them for review.

## Deployment

- **Frontend Application**: Deployed to Vercel at [https://emitra-two.vercel.app](https://emitra-two.vercel.app)
- **Backend Service**: Deployed to Render at [https://emitra-backend-lpg5.onrender.com/api/](https://emitra-backend-lpg5.onrender.com/api/)
- **Database**: PostgreSQL hosted on Neon DB.
- **CORS Handling**: Django settings allow the frontend domain and authorize the custom header `x-organization-id` in preflight OPTIONS requests.

## Local Setup

### Backend Setup
1. Clone the repository and navigate to the project directory.
2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
4. Seed the database with the default organization:
   ```bash
   python seed.py
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup
1. From the root directory, install npm packages:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Set the environment variable `VITE_API_URL` to point to the local Django server (`http://127.0.0.1:8000`) if needed, or leave it blank to default to proxy `/api` requests.

## Documentation

For a detailed dive into individual design layers, review the accompanying documentation files:
- **[MODEL.md](file:///d:/projects/Emitra/MODEL.md)**: Database schemas, model attributes, and relational diagram.
- **[DECISIONS.md](file:///d:/projects/Emitra/DECISIONS.md)**: Architectural patterns and design decisions (such as UI choices and schema mappings).
- **[TRADEOFFS.md](file:///d:/projects/Emitra/TRADEOFFS.md)**: Intentionally deferred systems (like background workers, active OCR pipelines, and JWT identity management).
- **[SOURCES.md](file:///d:/projects/Emitra/SOURCES.md)**: Realism research sources, emission factor guides (GHG Protocol, EPA), and unit conversions.

## Known Limitations

- **Header-Based Multi-Tenancy**: The application partitions data via the client-provided `X-Organization-ID` request header. This is a simplified boundary and does not replace cryptographic JWT token claims.
- **No Native Authentication**: The prototype focuses entirely on ingestion, data normalization, validation, and review logic. Authentication layers were omitted for MVP simplicity.
- **Synchronous Ingestion Loop**: Ingestion runs synchronously in the HTTP request-response cycle, which works for typical datasets (<1,000 rows) but would timeout for larger enterprise datasets.
- **Fixed Emission Factors**: Applies static emission factors defined in the codebase, requiring code updates to change rather than a dynamic database-backed lookup table.

## Tradeoffs

A complete summary of design decisions made due to the prototype's timeline includes:
- **Synchronous Processing over Background Queues**: Skipped Celery and Redis setup to keep infrastructure light and easily deployable on a free Render tier, acknowledging that large files (>10,000 rows) require async workers.
- **CSV Ingestion over Direct APIs or OCR**: Handled portal export files instead of building complex OCR parsers for PDF bills, focusing dev time on the calculations and audit history.
- **Header Tenancy over Auth Systems**: Utilized a tenant context header to test and prove multi-tenant database isolation without the overhead of user sign-up and authentication flows.

## Future Improvements

- **Authentication**: Implementing JWT authentication and deriving the organization context from user claims.
- **Asynchronous Workers**: Migrating the synchronous ingestion loop to a Celery background task queue to support large file volumes.
- **Dynamic Emission Factor Registry**: Storing emission factors in the database with date ranges to support historical factor variations and updates.
- **Expanded API Connectors**: Building native connectors to pull data directly from SAP OData web services or travel platform APIs.

## Submission Notes

This project was built as part of the Breathe ESG Tech Intern recruitment assignment. It is designed to demonstrate realistic data modeling, multi-tenant DB query isolation, unit conversion pipelines, calculation accuracy, and strict audit locking enforcement required in regulatory carbon compliance systems.
