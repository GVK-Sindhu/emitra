# Source Formats Research & Design

This document details the real-world formats researched for SAP, Utility bills, and Travel data, along with our sample data choices.

---

## 1. Real-World Source Formats Researched

### SAP ERP Procurement Exports
- **Real-World Shape:** SAP uses flat file formats (e.g. from ALV grid exports) or BAPIs. In global companies, configurations often mix German and English. Standard columns include:
  - `Werksnummer` / `Werks` (Plant Code)
  - `Material` / `Materialnummer` (Material Group / Fuel Type)
  - `Menge` (Quantity Purchased)
  - `Einheit` (Unit of Measure - e.g., `GAL`, `L`)
  - `Buchungsdatum` (Posting Date, often in `DD.MM.YYYY` format)
- **Our Implementation:** We built an English/German header-matching index and date normalizer. This handles variations like `Werksnummer` mapping to `Plant Code`.

### Utility Portal Exports
- **Real-World Shape:** Portal downloads (like PG&E Green Button Data or Duke Energy exports) contain CSV tables. Key items are Meter IDs, billing dates, usage (in kWh or Wh), and tariff groups.
- **Our Implementation:** We map utility usage to distinct billing cycles. The validation engine implements static threshold-based checks, automatically flagging any record indicating consumption exceeding 50,000 kWh. Rolling historical average checks were deferred for the MVP scope to reduce synchronous database lookup overhead.

### Travel Logs (Navan/Concur)
- **Real-World Shape:** Travel platform API exports (Concur Expense API, Navan Corporate Bookings) contain detailed transaction logs. When companies extract travel histories, distances are frequently missing. However, departure and destination airport IATA codes (e.g., JFK, SFO) are always present.
- **Our Implementation:** Our travel pipeline ingests flights, hotel nights, and ground transport. If distance is missing, we calculate the great-circle mileage between airport codes using the **Haversine formula**.

---

## 2. Mock Data Design Decisions
We created three sample datasets in the `sample_data/` directory to demonstrate:
1. **SAP:** Ingestion of German headers, conversion of gallons to liters, and flagging unrecognized fuels.
2. **Utility:** Reading multiple billing periods for the same Meter ID, standardizing units, and triggering the rolling spike validation check.
3. **Travel:** Distance estimation for flights with missing distances using airport lookup coordinates, validation checks for excessive hotel stays (>30 nights), and taxi transport carbon factors.

---

## 3. Limitations of this MVP
- **Precompiled Coordinate Dictionary:** The Haversine distance calculator uses a hardcoded coordinates map of major global airports (JFK, LAX, SFO, etc.). In production, this would be backed by an external geocoding API or a complete airport coordinates database table.
- **Tariff Factor Sensitivity:** Currently, utility emissions are calculated using a static regional grid average factor (0.38 kg CO2e / kWh). Production setups should integrate location-based grid intensity APIs (e.g., eGRID in the US or ElectricityMap) to adjust factors based on the hour and grid region of the Meter ID.

---

## 4. Why Problematic Rows Were Included

To simulate realistic corporate onboarding environments and validate system resilience under data-quality challenges observed during actual ESG reporting workflows, the sample datasets intentionally contain the following anomalies:

- **Duplicate procurement lines**: Emulates split invoices or partial delivery bookings common in material document ledgers.
- **Supplier-specific fuel codes**: Simulates localized naming conventions (`DSL`, `DFUEL`) where global master codes are missing.
- **Missing plant mappings**: Represents unmapped operational sites or expenses allocated directly to a corporate cost center.
- **Utility billing anomalies**: Zero-usage service fees, unmapped meter points, and consumption spike values.
- **Solar export credits**: Positive generation feedbacks that manifest as negative usage/financial credits.
- **Cancelled travel segments**: Travel bookings booked but voided prior to departure, which must be evaluated at 0 emissions to prevent carbon over-reporting.
- **Missing hotel checkout dates**: Tests validation response to incomplete booking transactions.
- **Missing travel distances**: Simulates TMS exports omitting flight mileage, necessitating coordinates-based distance estimation.
