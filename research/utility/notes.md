# Utility Electricity Ingestion Research Notes

This document provides staff-level engineering research and onboarding analysis for extracting and normalizing commercial utility billing data into Scope 2 indirect emissions.

---

## 1. Typical Export Structure

Commercial electricity data is rarely extracted via live smart-meter APIs due to fragmented utility grids. Instead, facilities teams download summary tables from provider billing portals (e.g., PG&E, ConEd, Duke Energy) or receive unified EDI (Electronic Data Interchange) 810 invoice transactions.

### Key Invoice Components
*   **Customer Metadata**: `AccountNumber`, `SiteName`, `BillingCycle`.
*   **Physical Delivery Point**: `Meter ID`, `ServicePointID`.
*   **Operational Consumption**: `Usage` (in kWh or MWh), `Billing Start`, `Billing End`, `Tariff` (rate class).
*   **Grid Peak Capacity**: `Demand_kW` (the peak power demand during the billing cycle, which determines infrastructure charges).
*   **Financials**: `BillAmount`, `Currency`.

---

## 2. Common Onboarding Pain Points

1.  **Non-Calendar Billing Cycles**: Utility meters are read in cycles that rarely align with standard calendar months (e.g., February 15 to March 14). Allocating emissions to annual or quarterly reporting boundaries requires splitting calculations proportionally by day.
2.  **Tariff Class Shifts**: Facilities switch rate classes (e.g., Commercial Peak, Off-Peak, Renewable Green Tariffs) mid-year. Because different tariffs may map to different grid carbon intensities (such as when buying certified green power), the calculation engine must track these changes.
3.  **Solar Feed-in Credits**: Large warehouses often generate solar power. The utility export contains negative usage records representing net exports to the grid (credit adjustments), which must not be confused with normal data collection failures.
4.  **Idle/Zero-Usage Facilities**: Unused warehouses still incur fixed service fees. The ledger shows a bill amount of e.g. `$75.00` but exactly `0 kWh` of usage.
5.  **Data Quality Inconsistencies**: Meter ID updates during physical replacement cause billing portals to output records with missing ServicePointIDs or empty account links.

---

## 3. Rationale for Problematic Sample Rows (`utility_export.csv`)

Our realistic `utility_export.csv` validates specific ingestion parsing capabilities:

*   **Row 1, 2, & 3 (Mid-Month Cycles - `MTR-IND-001`)**:
    *   *Why it exists:* Shows a continuous sequence of mid-month cycles (e.g. Feb 15 - Mar 14) for a warehouse. 
    *   *System validation:* Asserts that the ingestion engine preserves start and end dates and maps the emissions activity date to the billing cycle end date.
*   **Row 2 vs Row 1 (Tariff Shift - `Industrial Off-Peak` vs `Industrial Peak`)**:
    *   *Why it exists:* The utility company switched the customer's billing scheme to a time-of-use tariff.
    *   *System validation:* The system dynamically resolves the correct emission factor based on the tariff text.
*   **Row 4 & 5 (Unit conversion and Threshold Exception - `MTR-IND-002`)**:
    *   *Why it exists:* Munich R&D Lab uses high-power equipment. The April invoice was recorded in `MWh` (common for heavy loads), and the May invoice exceeded 50k kWh.
    *   *System validation:* Row 4 is normalized from `12 MWh` to `12,000 kWh` successfully. Row 5 (`65,000 kWh`) exceeds our static threshold (>50,000 kWh) and is flagged as `SUSPICIOUS`, highlighting a potential operational anomaly for analyst review.
*   **Row 6 (Solar Feedback Credit - `MTR-IND-003`)**:
    *   *Why it exists:* Denver office utilizes solar panels and fed back `1200 kWh` more than it consumed in May, resulting in a cost credit of `-$150.00`.
    *   *System validation:* Flags the row due to the negative quantity. The analyst must verify if this net credit is correct and approve it.
*   **Row 7 (Zero-Usage Service Fees - `MTR-IND-004`)**:
    *   *Why it exists:* Phoenix facility was empty during May, but the utility charged a `$75.00` fixed connection fee.
    *   *System validation:* Ingests the `0 kWh` record without failure, showing zero calculated emissions.
*   **Row 8 (Missing Service Point - `MTR-IND-005`)**:
    *   *Why it exists:* Occurs when a meter is newly installed and the billing system has not fully mapped the service point ID master record.
    *   *System validation:* Ingests the record but flags the missing ServicePointID as a data quality alert.

---

## 4. Real-World Limitations

*   **Grid Intensity Shifts**: Our MVP uses a static grid average factor of `0.38 kg CO2e / kWh`. In a mature audit setting, emission factors must vary by hourly grid mix (e.g., eGRID zip code lookup in the US, or ENTSO-E grid lookups in Europe) to support location-based Scope 2 methods.
*   **Billing Overlaps**: Simple ingestion loops do not detect if a supplier bills twice for the same meter period. Production systems require interval intersection algorithms to flag overlapping billing dates.

---

## 5. Technical Assumptions

*   **Location-Based Default**: Unless a renewable green tariff is explicitly mentioned, the system applies the local utility grid intensity factor (`0.38 kg CO2e/kWh`).
*   **Activity Date Mapping**: Emissions are assigned to the `Billing End` date, assuming this is when the electricity consumption cycle concludes for audit reporting.
