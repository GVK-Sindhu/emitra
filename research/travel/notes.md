# Corporate Business Travel Ingestion Research Notes

This document provides staff-level engineering research and onboarding analysis for corporate travel datasets representing Scope 3 Category 6 (Business Travel) emissions.

---

## 1. Typical Export Structure

Corporate travel data typically originates from Travel Management Systems (TMS) such as Navan, SAP Concur, or Corporate Travel Management (CTM). Instead of single consolidated files, enterprise accounting systems output separate transactional database tables to preserve double-entry audit records.

### A. Air Segments (`AirSegments.csv`)
Tracks flight bookings.
*   `TripID`, `SegmentID`, `EmployeeID`, `Airline`, `FlightNumber`, `DepartureAirport` (IATA code), `ArrivalAirport` (IATA code), `DepartureDate`, `ArrivalDate`, `ClassOfService` (Economy/Business/First), `Distance`, `DistanceUnit`, `Status` (Confirmed/Cancelled).

### B. Hotel Stays (`HotelStays.csv`)
Tracks hospitality bookings.
*   `TripID`, `HotelID`, `CheckInDate`, `CheckOutDate`, `NumberOfNights`, `HotelName`, `City`, `Country`.

### C. Ground Transport (`GroundTransport.csv`)
Tracks taxis, trains, and car rentals.
*   `TripID`, `TransportType` (Taxi/Train/Uber), `Vendor`, `Distance`, `Cost`.

---

## 2. Common Onboarding Pain Points

1.  **Missing Flight Distances**: Travel systems often omit exact mileage due to ticketing API limitations. Resolving missing distances using airport coordinates is a mandatory compliance requirement.
2.  **Cancelled or Re-routed Travel**: Bookings are frequently cancelled or updated. Ledgers will show "Cancelled" or "Void" transactions. If the parser ignores these status fields, it will over-calculate emissions for flights that were never taken.
3.  **Class of Service Adjustments**: Business and First Class flights consume more physical space/weight on planes and are allocated higher carbon weightings (e.g., a business class long-haul flight has an emissions factor multiplier compared to economy).
4.  **Ground Distance Inference**: Taxi receipts in travel expense systems contain costs (e.g. `$45.00`) but almost never list the mileage. Inferring distance from cost using standard regional averages is necessary to prevent scope gaps.
5.  **Hospitality Checkout Gaps**: Hotel reports often contain check-in and check-out dates, but fail to output the exact `NumberOfNights` column, requiring automated duration calculation.

---

## 3. Rationale for Problematic Sample Rows

### A. Air Segments (`AirSegments.csv`)
*   **Row 1 & 2 (Missing Distance & Duplicate Segments - `TR-00912`)**:
    *   *Why it exists:* A flight was booked from JFK to LAX, but the distance column was empty. The segment appears twice because of a ticketing re-issue.
    *   *System validation:* JFK-LAX distance is automatically estimated using the Haversine formula (~2475 miles). The duplicate flight segment is flagged in the system for double-counting verification.
*   **Row 4 (Cancelled Flight Segment - `TR-00918`)**:
    *   *Why it exists:* An employee cancelled a business trip to Chicago.
    *   *System validation:* The parser detects the `Cancelled` status, overrides calculations to `0.0 tCO2e`, and formats the activity type description accordingly, showing realistic compliance hygiene.
*   **Row 6 (Business-Class Short-Haul Flight - `TR-00922`)**:
    *   *Why it exists:* Employee flew business class from Atlanta to New York.
    *   *System validation:* The validator flags this. Short-haul domestic flights (< 300 miles) in business class are carbon-inefficient and often flagged for corporate travel policy violations.
*   **Row 7 & 8 (Multi-Leg Journey - `TR-00930`)**:
    *   *Why it exists:* Represents a multi-leg journey from New York (JFK) to Frankfurt (FRA) and then to Mumbai (BOM).
    *   *System validation:* Ingests and calculates emissions for both legs independently, preserving transactional fidelity.

### B. Hotel Stays (`HotelStays.csv`)
*   **Row 2 (Missing Number of Nights - `TR-00915`)**:
    *   *Why it exists:* Concur booking export omitted the nights field.
    *   *System validation:* The system automatically calculates duration by subtracting the check-in date (`12.05.2026`) from checkout (`14.05.2026`) to estimate `2 nights`, completing the calculations.
*   **Row 3 (Missing Checkout Date - `TR-00918`)**:
    *   *Why it exists:* Occurs when checkout dates are left blank due to check-out failures or incomplete bookings.
    *   *System validation:* Flags the row as suspicious due to missing checkout data, ensuring the analyst checks the record.
*   **Row 4 (Excessive Hotel Stay - `TR-00920`)**:
    *   *Why it exists:* Employee stayed 36 nights at Marriott SFO (long-term relocation).
    *   *System validation:* Triggers the suspicious stay check (>30 nights) to flag long-term stays that may represent corporate housing, which requires different emission factors.

### C. Ground Transport (`GroundTransport.csv`)
*   **Row 1 & 3 (Distance Inferred from Cost - `TR-00912` & `TR-00920`)**:
    *   *Why it exists:* Expensify logs show costs of `$45.00` and `$30.00` for taxi rides but contain no distance metric.
    *   *System validation:* The parser detects missing distance on taxi modes, applies a heuristic ($3.00/mile), and infers `15` and `10` miles respectively, ensuring calculation coverage.

---

## 4. Real-World Limitations

*   **Airport Database Exhaustiveness**: Our database uses a precompiled lookup of major hubs. Flights to secondary airports require integration with complete airport registries (e.g. OpenFlights database) or geocoding APIs.
*   **Ground Fuel Variances**: Taxi emissions assume a general average. Real-world audits must capture vehicle sizes (e.g., SUV vs Hybrid) to match exact emissions.

---

## 5. Technical Assumptions

*   **Haversine Distance**: Computes great-circle distance between coordinates, ignoring headwinds or flight patterns.
*   **Cost-per-Mile Heuristic**: Ground taxis are modeled at a flat `$3.00/mile` rate, assuming typical urban taxi/ridehail fee structures.
