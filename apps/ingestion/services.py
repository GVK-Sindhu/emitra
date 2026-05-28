import os
import pandas as pd
import numpy as np
from decimal import Decimal
from django.db import transaction
from django.db.models import Avg
from apps.ingestion.models import DataSource, RawRecord, IngestionStatus, ProcessingStatus, SourceType
from apps.emissions.models import EmissionRecord, ScopeCategory, ApprovalStatus
from apps.emissions.services import (
    clean_decimal,
    calculate_sap_emissions,
    calculate_utility_emissions,
    calculate_travel_emissions,
    validate_record
)
import datetime

class NormalizationError(Exception):
    """Exception raised when raw record normalization fails validation or is blank."""
    pass

def parse_date(date_str) -> datetime.date | None:
    """
    Parses date string in formats DD.MM.YYYY, YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY etc.
    """
    if date_str is None or str(date_str).strip() == '' or str(date_str).lower() == 'nan' or str(date_str).lower() == 'none':
        return None
    date_str = str(date_str).strip()
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

# Header Mapping for German SAP Exports to Standardized English
SAP_HEADER_MAPPING = {
    'werkcode': 'Plant Code',
    'werksnummer': 'Plant Code',
    'plant code': 'Plant Code',
    'plantcode': 'Plant Code',
    'materialnummer': 'Material',
    'materialnumber': 'Material',
    'material': 'Material',
    'menge': 'Fuel Quantity',
    'fuel quantity': 'Fuel Quantity',
    'einheit': 'Fuel Unit',
    'fuel unit': 'Fuel Unit',
    'buchungsdatum': 'Posting Date',
    'posting date': 'Posting Date',
    'lieferant': 'Vendor',
    'vendor': 'Vendor',
    'suppliername': 'Vendor',
    'suppliercode': 'Supplier Code',
    'supplier code': 'Supplier Code',
    'kostenstelle': 'Cost Center',
    'cost center': 'Cost Center',
    'purchaseordernumber': 'Purchase Order Number',
    'purchase order number': 'Purchase Order Number',
    'documentnumber': 'Document Number',
    'document number': 'Document Number',
    'itemnumber': 'Item Number',
    'item number': 'Item Number',
    'movementtype': 'Movement Type',
    'movement type': 'Movement Type'
}

def ingest_data_source(datasource_id):
    """
    Ingests and normalizes an uploaded file row-by-row.
    Updates the DataSource status and handles line-level errors gracefully.
    """
    try:
        datasource = DataSource.objects.get(pk=datasource_id)
    except DataSource.DoesNotExist:
        return
        
    datasource.ingestion_status = IngestionStatus.PROCESSING
    datasource.save()
    
    file_path = datasource.uploaded_file.path
    if not os.path.exists(file_path):
        datasource.ingestion_status = IngestionStatus.FAILED
        datasource.error_message = f"File not found at path: {file_path}"
        datasource.save()
        return

    try:
        # Load CSV using pandas
        # Keep everything as string initially to prevent auto-truncation/corrupt formatting of text columns
        df = pd.read_csv(file_path, dtype=str)
        df = df.replace({np.nan: None}) # Clean pandas NaNs
    except Exception as e:
        datasource.ingestion_status = IngestionStatus.FAILED
        datasource.error_message = f"Failed to parse CSV file: {str(e)}"
        datasource.save()
        return

    # Ingest rows
    raw_records_created = []
    
    with transaction.atomic():
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            # Clean values: convert pandas/numpy NaNs and "nan" strings to None for valid JSON serialization
            cleaned_row = {}
            for k, v in row_dict.items():
                if k is not None:
                    k_str = str(k).strip()
                    if pd.isna(v) or str(v).strip().lower() in ('nan', 'none', ''):
                        cleaned_row[k_str] = None
                    else:
                        cleaned_row[k_str] = str(v).strip()
            
            # For SAP, normalize German headers
            if datasource.source_type == SourceType.SAP:
                normalized_row = {}
                for k, v in cleaned_row.items():
                    k_lower = k.lower()
                    mapped_key = SAP_HEADER_MAPPING.get(k_lower, k)
                    normalized_row[mapped_key] = v
                cleaned_row = normalized_row

            # Save raw record
            raw_rec = RawRecord.objects.create(
                datasource=datasource,
                raw_json=cleaned_row,
                processing_status=ProcessingStatus.UNPROCESSED
            )
            raw_records_created.append(raw_rec)

    # Process/Normalize each raw record
    success_count = 0
    fail_count = 0
    
    for raw_rec in raw_records_created:
        try:
            process_single_raw_record(raw_rec)
            success_count += 1
        except NormalizationError:
            fail_count += 1
        except Exception as e:
            raw_rec.processing_status = ProcessingStatus.FAILED
            raw_rec.error_message = f"System normalization crash: {str(e)}"
            raw_rec.save()
            fail_count += 1
            
    # Finalize Ingestion Status
    if fail_count == len(raw_records_created) and fail_count > 0:
        datasource.ingestion_status = IngestionStatus.FAILED
        datasource.error_message = "All records in the file failed processing."
    else:
        datasource.ingestion_status = IngestionStatus.SUCCESS
        if fail_count > 0:
            datasource.error_message = f"Completed with {fail_count} failures out of {len(raw_records_created)} rows."
            
    datasource.save()

def process_single_raw_record(raw_record):
    """
    Normalizes a single RawRecord, runs validations, and saves the resulting EmissionRecord.
    """
    datasource = raw_record.datasource
    org = datasource.organization
    raw_json = raw_record.raw_json
    source_type = datasource.source_type

    # A. Check if completely empty/blank row (all values are None or empty/whitespace strings)
    if not raw_json or all(v is None or str(v).strip() == "" for v in raw_json.values()):
        with transaction.atomic():
            raw_record.processing_status = ProcessingStatus.FAILED
            raw_record.error_message = "Blank row ignored"
            raw_record.save()
            # Prevent creation and ensure we clean up any existing duplicate/processed records
            EmissionRecord.objects.filter(raw_record=raw_record).delete()
        raise NormalizationError("Blank row detected")

    # 1. Base validation check (missing values, negatives, invalid airport codes)
    is_suspicious, suspicious_reason = validate_record(source_type, raw_json)
    
    # B. If required fields are missing, mark as FAILED and abort EmissionRecord creation
    if suspicious_reason and "Missing required field" in suspicious_reason:
        with transaction.atomic():
            raw_record.processing_status = ProcessingStatus.FAILED
            raw_record.error_message = suspicious_reason
            raw_record.save()
            EmissionRecord.objects.filter(raw_record=raw_record).delete()
        raise NormalizationError(suspicious_reason)

    reasons = [suspicious_reason] if suspicious_reason else []

    calc_results = {}
    scope = None
    original_qty = Decimal('0.0')
    original_unit = ''
    activity_date = None
    billing_start = None
    billing_end = None

    # 2. Ingest by Source Type
    if source_type == SourceType.SAP:
        scope = ScopeCategory.SCOPE1
        material = raw_json.get('Material', '')
        qty_str = raw_json.get('Fuel Quantity', '0')
        unit = raw_json.get('Fuel Unit', 'L')
        
        original_qty = clean_decimal(qty_str)
        original_unit = unit
        
        calc_results = calculate_sap_emissions(material, original_qty, original_unit)
        activity_date = parse_date(raw_json.get('Posting Date', ''))

    elif source_type == SourceType.UTILITY:
        scope = ScopeCategory.SCOPE2
        meter_id = raw_json.get('Meter ID', '')
        usage_str = raw_json.get('Usage', '0')
        unit = raw_json.get('Unit', 'kWh')
        tariff = raw_json.get('Tariff', 'Grid')
        
        original_qty = clean_decimal(usage_str)
        original_unit = unit
        
        calc_results = calculate_utility_emissions(original_qty, original_unit, tariff)
        billing_start = parse_date(raw_json.get('Billing Start', ''))
        billing_end = parse_date(raw_json.get('Billing End', ''))
        activity_date = billing_end

    elif source_type == SourceType.TRAVEL:
        scope = ScopeCategory.SCOPE3
        flight_type = raw_json.get('Flight Type', raw_json.get('ClassOfService', ''))
        from_ap = raw_json.get('From Airport', raw_json.get('DepartureAirport', ''))
        to_ap = raw_json.get('To Airport', raw_json.get('ArrivalAirport', ''))
        distance_str = raw_json.get('Distance', '0')
        dist_unit = str(raw_json.get('Distance Unit', raw_json.get('DistanceUnit', 'miles'))).strip().lower()
        nights_str = raw_json.get('Hotel Nights', raw_json.get('NumberOfNights', '0'))
        ground = raw_json.get('Ground Transport', raw_json.get('TransportType', ''))
        status_val = str(raw_json.get('Status', '')).strip().lower()

        # In case of missing NumberOfNights in HotelStays but dates are present:
        if clean_decimal(nights_str) == 0 and 'CheckInDate' in raw_json and 'CheckOutDate' in raw_json:
            in_date = parse_date(raw_json.get('CheckInDate'))
            out_date = parse_date(raw_json.get('CheckOutDate'))
            if in_date and out_date:
                nights_str = str((out_date - in_date).days)
                
        # In case of Ground Transport with cost but no distance:
        cost_str = raw_json.get('Cost', '')
        if ground and clean_decimal(distance_str) == 0 and cost_str:
            cost_val = clean_decimal(cost_str)
            # Estimate: $3.00 per mile for taxis/ridehails
            distance_str = str(cost_val / Decimal('3.0'))

        original_qty = clean_decimal(distance_str)
        if dist_unit in ['km', 'kilometers', 'kilometres']:
            original_qty = original_qty * Decimal('0.621371')
        original_unit = 'miles'
        
        # Special logic: Cancelled flight segments result in 0 emissions
        if status_val == 'cancelled' or status_val == 'void':
            calc_results = {
                'normalized_quantity': Decimal('0.0'),
                'normalized_unit': 'kg CO2e eq',
                'emission_factor': Decimal('0.0'),
                'calculated_emission': Decimal('0.0'),
                'activity_type': f"Business Travel - Cancelled Flight (Flight {raw_json.get('FlightNumber', '')})"
            }
        else:
            calc_results = calculate_travel_emissions(
                flight_type=flight_type,
                from_airport=from_ap,
                to_airport=to_ap,
                distance=original_qty,
                hotel_nights=clean_decimal(nights_str),
                ground_transport=ground
            )
            
        activity_date_str = raw_json.get('Travel Date', raw_json.get('Date', raw_json.get('DepartureDate', raw_json.get('CheckInDate', ''))))
        activity_date = parse_date(activity_date_str)
        if not activity_date and datasource.uploaded_at:
            activity_date = datasource.uploaded_at.date()

    # 3. Create clean normalized record
    # We run in atomic block to update both raw record status and create the emission record
    with transaction.atomic():
        # Combine reasons
        combined_reason = "; ".join(reasons) if reasons else None
        
        # Check if an emission record already exists for this raw record (in case of re-processing)
        emission_rec, created = EmissionRecord.objects.get_or_create(
            raw_record=raw_record,
            defaults={
                'organization': org,
                'scope_category': scope,
                'activity_type': calc_results.get('activity_type', 'Unknown'),
                'quantity': original_qty,
                'unit': original_unit,
                'normalized_quantity': calc_results.get('normalized_quantity', Decimal('0.0')),
                'normalized_unit': calc_results.get('normalized_unit', ''),
                'emission_factor': calc_results.get('emission_factor', Decimal('0.0')),
                'calculated_emission': calc_results.get('calculated_emission', Decimal('0.0')),
                'suspicious_flag': is_suspicious,
                'suspicious_reason': combined_reason,
                'approval_status': ApprovalStatus.PENDING,
                'locked_for_audit': False,
                'activity_date': activity_date,
                'billing_period_start': billing_start,
                'billing_period_end': billing_end,
            }
        )
        
        if not created:
            # Update fields
            emission_rec.scope_category = scope
            emission_rec.activity_type = calc_results.get('activity_type', 'Unknown')
            emission_rec.quantity = original_qty
            emission_rec.unit = original_unit
            emission_rec.normalized_quantity = calc_results.get('normalized_quantity', Decimal('0.0'))
            emission_rec.normalized_unit = calc_results.get('normalized_unit', '')
            emission_rec.emission_factor = calc_results.get('emission_factor', Decimal('0.0'))
            emission_rec.calculated_emission = calc_results.get('calculated_emission', Decimal('0.0'))
            emission_rec.suspicious_flag = is_suspicious
            emission_rec.suspicious_reason = combined_reason
            # Reset approval if re-processed
            emission_rec.approval_status = ApprovalStatus.PENDING
            emission_rec.locked_for_audit = False
            emission_rec.activity_date = activity_date
            emission_rec.billing_period_start = billing_start
            emission_rec.billing_period_end = billing_end
            emission_rec.save()

        # Update raw record status
        raw_record.processing_status = ProcessingStatus.SUSPICIOUS if is_suspicious else ProcessingStatus.SUCCESS
        raw_record.error_message = combined_reason
        raw_record.save()
