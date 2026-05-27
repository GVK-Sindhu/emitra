import math
import re
from decimal import Decimal

# Major airport coordinates database for Haversine distance calculation (IATA Code -> (Lat, Long))
AIRPORT_COORDINATES = {
    'JFK': (40.6398, -73.7789),
    'LAX': (33.9416, -118.4085),
    'ORD': (41.9742, -87.9073),
    'SFO': (37.6213, -122.3790),
    'ATL': (33.6407, -84.4277),
    'LHR': (51.4700, -0.4543),
    'DXB': (25.2532, 55.3657),
    'CDG': (49.0097, 2.5479),
    'SIN': (1.3644, 103.9915),
    'HND': (35.5494, 139.7798),
    'SYD': (-33.9461, 151.1772),
    'BOM': (19.0896, 72.8656),
    'DEL': (28.5562, 77.1000),
    'DFW': (32.8998, -97.0403),
    'DEN': (39.8561, -104.6737),
    'SEA': (47.4502, -122.3088),
    'EWR': (40.6895, -74.1745),
    'BOS': (42.3656, -71.0096),
    'MIA': (25.7959, -80.2870),
    'FRA': (50.0379, 8.5622),
    'AMS': (52.3105, 4.7683),
    'IAD': (38.9531, -77.4565),
    'IAH': (29.9802, -95.3397),
    'SAN': (32.7338, -117.1933),
}

# Standardized emission factors (kg CO2e per normalized unit)
EMISSION_FACTORS = {
    # Scope 1 (Direct Fuels, normalized unit: L for liquids, m3 for gas)
    'diesel': Decimal('2.68'),       # kg CO2e / Litre
    'petrol': Decimal('2.31'),       # kg CO2e / Litre
    'gasoline': Decimal('2.31'),     # kg CO2e / Litre
    'natural_gas': Decimal('2.02'),  # kg CO2e / m3
    'default_fuel': Decimal('2.50'), # Default fallback factor

    # Scope 2 (Grid Electricity, normalized unit: kWh)
    'electricity_grid': Decimal('0.38'),      # kg CO2e / kWh
    'electricity_green': Decimal('0.05'),     # kg CO2e / kWh
    'electricity_peak': Decimal('0.45'),      # kg CO2e / kWh

    # Scope 3 (Business Travel)
    'flight_short_haul': Decimal('0.25'),     # kg CO2e / passenger-mile (< 300 miles)
    'flight_long_haul': Decimal('0.15'),      # kg CO2e / passenger-mile (>= 300 miles)
    'hotel_night': Decimal('10.40'),          # kg CO2e / night
    'ground_taxi': Decimal('0.30'),            # kg CO2e / mile
    'ground_train': Decimal('0.10'),           # kg CO2e / mile
    'ground_default': Decimal('0.20'),         # kg CO2e / mile
}

def clean_decimal(val) -> Decimal:
    """Helper to convert any input cleanly to Decimal."""
    if val is None or str(val).strip() == '' or str(val).lower() == 'nan':
        return Decimal('0.0')
    try:
        # Strip currency symbols, commas, or extra whitespace
        cleaned = re.sub(r'[^\d\.\-]', '', str(val))
        return Decimal(cleaned)
    except Exception:
        return Decimal('0.0')

def haversine_distance(from_code: str, to_code: str) -> float:
    """
    Calculates the great-circle distance between two airports in miles.
    Utilizes latitude and longitude coordinates.
    """
    if not from_code or not to_code:
        return 0.0
    
    from_code = str(from_code).strip().upper()
    to_code = str(to_code).strip().upper()
    
    if from_code not in AIRPORT_COORDINATES or to_code not in AIRPORT_COORDINATES:
        return 0.0
        
    lat1, lon1 = AIRPORT_COORDINATES[from_code]
    lat2, lon2 = AIRPORT_COORDINATES[to_code]
    
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def normalize_fuel_unit(quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    """
    Normalizes fuel quantity units to Litres (L) for liquids or cubic meters (m3) for gas.
    Supports gallons, liters, m3, cubic meters, etc.
    """
    u = str(unit).strip().lower()
    
    # Gallons -> Litres (1 gal = 3.78541 L)
    if u in ['gal', 'gln', 'gallon', 'gallons']:
        return quantity * Decimal('3.78541'), 'L'
    # Litres / Liters -> L
    elif u in ['l', 'litres', 'liters', 'ltr']:
        return quantity, 'L'
    # Gaseous cubic meters -> m3
    elif u in ['m3', 'cbm', 'cubic meters', 'cubic meter']:
        return quantity, 'm3'
    
    # Fallback/Default
    return quantity, unit

def normalize_electricity_unit(usage: Decimal, unit: str) -> tuple[Decimal, str]:
    """
    Normalizes utility usage to kWh. Supports Wh, kWh, MWh.
    """
    u = str(unit).strip().lower()
    
    # Wh -> kWh
    if u in ['wh', 'watt-hours', 'watt-hour']:
        return usage / Decimal('1000.0'), 'kWh'
    # MWh -> kWh
    elif u in ['mwh', 'megawatt-hours', 'megawatt-hour']:
        return usage * Decimal('1000.0'), 'kWh'
    # kWh -> kWh
    elif u in ['kwh', 'kilowatt-hours', 'kilowatt-hour']:
        return usage, 'kWh'
        
    return usage, 'kWh'

def calculate_sap_emissions(material: str, quantity: Decimal, unit: str) -> dict:
    """
    Scope 1 - Direct combustion emissions.
    Standardizes fuel units and applies emission factors.
    """
    normalized_qty, normalized_unit = normalize_fuel_unit(quantity, unit)
    
    mat = str(material).strip().lower()
    factor_key = 'default_fuel'
    
    if 'diesel' in mat:
        factor_key = 'diesel'
    elif 'petrol' in mat or 'gasoline' in mat:
        factor_key = 'petrol'
    elif 'natural gas' in mat or 'gas' in mat:
        # Check if natural gas is in m3, otherwise warn/suspicious
        factor_key = 'natural_gas'
        
    factor = EMISSION_FACTORS.get(factor_key, EMISSION_FACTORS['default_fuel'])
    
    # calculated_emission = (qty * factor) / 1000 (converts kg to Metric Tons)
    calculated_emission = (normalized_qty * factor) / Decimal('1000.0')
    
    return {
        'normalized_quantity': normalized_qty,
        'normalized_unit': normalized_unit,
        'emission_factor': factor,
        'calculated_emission': calculated_emission,
        'activity_type': f"Fuel - {material.title()}"
    }

def calculate_utility_emissions(usage: Decimal, unit: str, tariff: str) -> dict:
    """
    Scope 2 - Purchased electricity indirect emissions.
    """
    normalized_qty, normalized_unit = normalize_electricity_unit(usage, unit)
    
    tar = str(tariff).strip().lower()
    factor_key = 'electricity_grid'
    
    if 'green' in tar or 'renewable' in tar:
        factor_key = 'electricity_green'
    elif 'peak' in tar:
        factor_key = 'electricity_peak'
        
    factor = EMISSION_FACTORS.get(factor_key, EMISSION_FACTORS['electricity_grid'])
    
    # calculated_emission = (qty * factor) / 1000 (kg to Metric Tons)
    calculated_emission = (normalized_qty * factor) / Decimal('1000.0')
    
    return {
        'normalized_quantity': normalized_qty,
        'normalized_unit': normalized_unit,
        'emission_factor': factor,
        'calculated_emission': calculated_emission,
        'activity_type': f"Electricity - {tariff.title() if tariff else 'Grid'}"
    }

def calculate_travel_emissions(
    flight_type: str, 
    from_airport: str, 
    to_airport: str, 
    distance: Decimal, 
    hotel_nights: Decimal, 
    ground_transport: str
) -> dict:
    """
    Scope 3 - Corporate Business Travel (Flights, Hotels, Ground Transport).
    """
    total_kg_co2e = Decimal('0.0')
    activity_details = []
    
    # 1. Flight Calculations
    # If distance is empty but airport codes are present, estimate using Haversine
    dist_val = clean_decimal(distance)
    if dist_val == 0 and from_airport and to_airport:
        calculated_dist = haversine_distance(from_airport, to_airport)
        dist_val = Decimal(f"{calculated_dist:.2f}")
        activity_details.append(f"Flight (Est: {dist_val} mi)")
    else:
        activity_details.append(f"Flight ({dist_val} mi)")
        
    if dist_val > 0:
        # short haul vs long haul limit is 300 miles
        f_type = 'flight_short_haul' if dist_val < 300 else 'flight_long_haul'
        factor = EMISSION_FACTORS[f_type]
        total_kg_co2e += dist_val * factor

    # 2. Hotel Nights Calculations
    nights_val = clean_decimal(hotel_nights)
    if nights_val > 0:
        total_kg_co2e += nights_val * EMISSION_FACTORS['hotel_night']
        activity_details.append(f"Hotel ({int(nights_val)} nights)")

    # 3. Ground Transport Calculations
    # Ground transport could be a numeric distance or a string like "Taxi" / "Train"
    gt_val = str(ground_transport).strip().lower()
    gt_distance = Decimal('0.0')
    gt_factor = EMISSION_FACTORS['ground_default']
    
    if gt_val:
        # check if it is numeric
        cleaned_gt = re.sub(r'[^\d\.]', '', gt_val)
        if cleaned_gt:
            gt_distance = Decimal(cleaned_gt)
            gt_factor = EMISSION_FACTORS['ground_default']
            activity_details.append(f"Ground ({gt_distance} mi)")
        else:
            # Estimate ground distance/emissions based on mode
            if 'train' in gt_val or 'rail' in gt_val:
                gt_distance = Decimal('30.0') # Assumed default travel distance
                gt_factor = EMISSION_FACTORS['ground_train']
                activity_details.append("Ground (Train Est: 30 mi)")
            elif 'taxi' in gt_val or 'cab' in gt_val or 'uber' in gt_val or 'lyft' in gt_val or 'car' in gt_val:
                gt_distance = Decimal('15.0')
                gt_factor = EMISSION_FACTORS['ground_taxi']
                activity_details.append("Ground (Taxi Est: 15 mi)")
                
        total_kg_co2e += gt_distance * gt_factor

    # Normalize total travel to "passenger-miles" (p-mi) or similar metric equivalent
    # We sum flight distance, ground distance, and convert hotel nights to passenger-mile carbon equivalent
    # For reporting simplicity, normalized_quantity = total_kg_co2e / 0.15 (arbitrary index)
    # But cleaner to keep normalized_quantity = total_kg_co2e, factor = 1.0 kg CO2e / unit
    normalized_qty = total_kg_co2e
    factor = Decimal('1.000000')
    calculated_emission = total_kg_co2e / Decimal('1000.0')
    
    activity_type = "Business Travel (" + ", ".join(activity_details) + ")" if activity_details else "Business Travel"
    
    return {
        'normalized_quantity': normalized_qty,
        'normalized_unit': 'kg CO2e eq',
        'emission_factor': factor,
        'calculated_emission': calculated_emission,
        'activity_type': activity_type
    }

def validate_record(source_type: str, raw_json: dict) -> tuple[bool, str]:
    """
    Evaluates raw record fields to check for unrealistic, incomplete, or suspicious values.
    Returns (suspicious_flag: bool, suspicious_reason: str)
    """
    suspicious = False
    reasons = []

    # General checks for negative values
    for k, v in raw_json.items():
        # check if it is numeric and negative
        if v is not None:
            try:
                # Remove common currency/unit signs and check if negative
                str_v = str(v).strip()
                if str_v.startswith('-') and clean_decimal(str_v) < 0:
                    suspicious = True
                    reasons.append(f"Negative value detected in field '{k}': {v}")
            except Exception:
                pass

    if source_type == 'SAP':
        # Mandatory fields
        material = raw_json.get('Material', raw_json.get('Materialnummer', ''))
        quantity_str = raw_json.get('Fuel Quantity', raw_json.get('Menge', ''))
        unit = raw_json.get('Fuel Unit', raw_json.get('Einheit', ''))
        
        if not material:
            suspicious = True
            reasons.append("Missing required field: Material")
        if not quantity_str:
            suspicious = True
            reasons.append("Missing required field: Fuel Quantity")
            
        qty = clean_decimal(quantity_str)
        normalized_qty, _ = normalize_fuel_unit(qty, unit)
        
        # High quantity check (> 100,000 Liters)
        if normalized_qty > 100000:
            suspicious = True
            reasons.append(f"Fuel quantity exceeds threshold (>100k L): {normalized_qty:.2f} L")
            
        # Unrecognized Material check
        mat_lower = str(material).lower()
        if not any(f in mat_lower for f in ['diesel', 'petrol', 'gasoline', 'natural gas', 'gas']):
            suspicious = True
            reasons.append(f"Unrecognized fuel material type: '{material}' (Default factor applied)")

    elif source_type == 'UTILITY':
        meter_id = raw_json.get('Meter ID', '')
        usage_str = raw_json.get('Usage', '')
        unit = raw_json.get('Unit', '')
        
        if not meter_id:
            suspicious = True
            reasons.append("Missing required field: Meter ID")
        if not usage_str:
            suspicious = True
            reasons.append("Missing required field: Usage")
            
        usage = clean_decimal(usage_str)
        normalized_usage, _ = normalize_electricity_unit(usage, unit)
        
        # High electricity usage check (> 50,000 kWh in one billing period)
        if normalized_usage > 50000:
            suspicious = True
            reasons.append(f"Electricity usage exceeds threshold (>50k kWh): {normalized_usage:.2f} kWh")

        # Rolling average check is deferred for MVP scope; only threshold checks (>50k kWh) are active
        pass

    elif source_type == 'TRAVEL':
        import datetime
        def local_parse(d_str):
            if not d_str: return None
            for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try: return datetime.datetime.strptime(str(d_str).strip(), fmt).date()
                except ValueError: pass
            return None

        from_ap = str(raw_json.get('From Airport', raw_json.get('DepartureAirport', ''))).strip().upper()
        to_ap = str(raw_json.get('To Airport', raw_json.get('ArrivalAirport', ''))).strip().upper()
        hotel_nights_str = raw_json.get('Hotel Nights', raw_json.get('NumberOfNights', '0'))
        distance_str = raw_json.get('Distance', '')
        status_val = str(raw_json.get('Status', '')).strip().lower()

        # Check airport codes validity
        if from_ap and (len(from_ap) != 3 or from_ap not in AIRPORT_COORDINATES):
            suspicious = True
            reasons.append(f"Invalid or unsupported source airport code: '{from_ap}'")
        if to_ap and (len(to_ap) != 3 or to_ap not in AIRPORT_COORDINATES):
            suspicious = True
            reasons.append(f"Invalid or unsupported destination airport code: '{to_ap}'")
            
        # Unrealistic hotel stay (> 30 nights) or missing hotel checkout date
        if 'CheckInDate' in raw_json and not raw_json.get('CheckOutDate') and hotel_nights_str == '0':
            suspicious = True
            reasons.append("Missing hotel checkout date")
            
        nights = clean_decimal(hotel_nights_str)
        if nights == 0 and 'CheckInDate' in raw_json and 'CheckOutDate' in raw_json:
            in_date = local_parse(raw_json.get('CheckInDate'))
            out_date = local_parse(raw_json.get('CheckOutDate'))
            if in_date and out_date:
                nights = Decimal((out_date - in_date).days)

        if nights > 30:
            suspicious = True
            reasons.append(f"Suspiciously long hotel stay: {int(nights)} nights")
            
        # Distance checks
        dist = clean_decimal(distance_str)
        if status_val != 'cancelled' and status_val != 'void':
            if (from_ap or to_ap) and not distance_str and (from_ap not in AIRPORT_COORDINATES or to_ap not in AIRPORT_COORDINATES):
                suspicious = True
                reasons.append("Distance is missing, and unable to estimate due to missing airport coordinates")

    reason_str = "; ".join(reasons) if reasons else None
    return suspicious, reason_str
