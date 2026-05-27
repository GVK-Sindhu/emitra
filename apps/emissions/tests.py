from django.test import TestCase
from decimal import Decimal
from apps.organizations.models import Organization
from apps.ingestion.models import DataSource, RawRecord, SourceType
from apps.emissions.models import EmissionRecord, ScopeCategory, ApprovalStatus
from apps.audits.models import AuditLog
from apps.emissions.services import (
    normalize_fuel_unit,
    normalize_electricity_unit,
    haversine_distance,
    calculate_sap_emissions,
    calculate_utility_emissions,
    calculate_travel_emissions,
    validate_record
)

class ESGPlatformTests(TestCase):
    
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.datasource_sap = DataSource.objects.create(
            organization=self.org,
            source_type=SourceType.SAP,
            uploaded_file="test_sap.csv"
        )
        self.datasource_utility = DataSource.objects.create(
            organization=self.org,
            source_type=SourceType.UTILITY,
            uploaded_file="test_utility.csv"
        )
        self.datasource_travel = DataSource.objects.create(
            organization=self.org,
            source_type=SourceType.TRAVEL,
            uploaded_file="test_travel.csv"
        )

    def test_unit_normalization(self):
        # 1. Fuel Normalization (Gallons -> Liters)
        qty, unit = normalize_fuel_unit(Decimal('10.0'), 'gallons')
        self.assertAlmostEqual(float(qty), 37.8541, places=4)
        self.assertEqual(unit, 'L')

        # 2. Electricity Normalization (MWh -> kWh)
        qty, unit = normalize_electricity_unit(Decimal('1.5'), 'MWh')
        self.assertEqual(qty, Decimal('1500.0'))
        self.assertEqual(unit, 'kWh')

    def test_haversine_distance(self):
        # LAX to JFK is approx 2475 miles
        dist = haversine_distance('LAX', 'JFK')
        self.assertGreater(dist, 2400)
        self.assertLess(dist, 2500)

        # Invalid or missing airport codes return 0.0
        self.assertEqual(haversine_distance('LAX', 'INVALID'), 0.0)

    def test_sap_calculations(self):
        # Test diesel calculation
        res = calculate_sap_emissions('Diesel Fuel', Decimal('100.0'), 'litres')
        # 100 L * 2.68 kg CO2e / L = 268 kg CO2e = 0.268 metric tons CO2e
        self.assertEqual(res['normalized_quantity'], Decimal('100.0'))
        self.assertEqual(res['normalized_unit'], 'L')
        self.assertEqual(res['calculated_emission'], Decimal('0.268'))

    def test_utility_calculations(self):
        res = calculate_utility_emissions(Decimal('1000.0'), 'kWh', 'Grid')
        # 1000 kWh * 0.38 kg CO2e / kWh = 380 kg CO2e = 0.38 metric tons CO2e
        self.assertEqual(res['calculated_emission'], Decimal('0.380'))

    def test_travel_calculations_with_haversine(self):
        res = calculate_travel_emissions(
            flight_type='Domestic',
            from_airport='LAX',
            to_airport='JFK',
            distance=Decimal('0.0'), # empty distance
            hotel_nights=Decimal('5'),
            ground_transport='Taxi'
        )
        # Verify flight distance is estimated using coordinates
        # LAX-JFK distance is approx 2475 miles. Since > 300 miles, long-haul factor 0.15 is used
        # 2475 * 0.15 = 371.25 kg CO2e
        # Hotel: 5 nights * 10.4 kg CO2e / night = 52.0 kg CO2e
        # Ground: Taxi default = 15 miles * 0.30 kg CO2e / mile = 4.5 kg CO2e
        # Total kg CO2e = 371.25 + 52 + 4.5 = 427.75 kg CO2e = 0.42775 metric tons CO2e
        self.assertGreater(res['calculated_emission'], Decimal('0.40'))
        self.assertLess(res['calculated_emission'], Decimal('0.45'))

    def test_record_validation(self):
        # 1. Check negative values
        suspicious, reason = validate_record('SAP', {
            'Material': 'Diesel',
            'Fuel Quantity': '-100',
            'Fuel Unit': 'L'
        })
        self.assertTrue(suspicious)
        self.assertIn("Negative value detected", reason)

        # 2. Check extreme quantities
        suspicious, reason = validate_record('SAP', {
            'Material': 'Diesel',
            'Fuel Quantity': '200000', # 200,000 Liters
            'Fuel Unit': 'L'
        })
        self.assertTrue(suspicious)
        self.assertIn("Fuel quantity exceeds threshold", reason)

    def test_travel_distance_conversion_ingestion(self):
        # Construct raw record representing travel segment in kilometers
        raw_rec = RawRecord.objects.create(
            datasource=self.datasource_travel,
            raw_json={
                'Employee ID': 'EMP-1001',
                'Flight Type': 'Domestic',
                'From Airport': 'JFK',
                'To Airport': 'LAX',
                'Distance': '100',
                'Distance Unit': 'km',
                'Hotel Nights': '0',
                'Ground Transport': '',
                'Travel Date': '12.05.2026'
            },
            processing_status='UNPROCESSED'
        )
        
        # We call process_single_raw_record, which performs the conversion
        from apps.ingestion.services import process_single_raw_record
        process_single_raw_record(raw_rec)
        
        # Retrieve normalized emission record
        emission_rec = EmissionRecord.objects.get(raw_record=raw_rec)
        
        # 100 km converted to miles is approx 62.1371 miles
        self.assertAlmostEqual(float(emission_rec.quantity), 62.1371, places=3)
        self.assertEqual(emission_rec.unit, 'miles')
        self.assertEqual(str(emission_rec.activity_date), '2026-05-12')

    def test_audit_trail_generation(self):
        # Create an initial record
        raw_rec = RawRecord.objects.create(
            datasource=self.datasource_sap,
            raw_json={'Material': 'Diesel', 'Fuel Quantity': '100', 'Fuel Unit': 'L'},
            processing_status='SUCCESS'
        )
        
        record = EmissionRecord.objects.create(
            organization=self.org,
            raw_record=raw_rec,
            scope_category=ScopeCategory.SCOPE1,
            activity_type="Fuel - Diesel",
            quantity=Decimal('100.0'),
            unit="L",
            normalized_quantity=Decimal('100.0'),
            normalized_unit="L",
            emission_factor=Decimal('2.68'),
            calculated_emission=Decimal('0.268'),
            suspicious_flag=False,
            approval_status=ApprovalStatus.PENDING,
            locked_for_audit=False
        )

        # Let's perform an update through simulated analyst edit
        record.quantity = Decimal('150.0')
        record.normalized_quantity = Decimal('150.0')
        record.calculated_emission = Decimal('0.402')
        record._changed_by = "analyst@test.com"
        record._change_reason = "Corrected diesel fuel delivery amount based on invoice."
        record.save()

        # Verify audit record is saved
        audit = AuditLog.objects.filter(emission_record=record).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.changed_by, "analyst@test.com")
        self.assertEqual(audit.old_value['quantity'], '100.0000')
        self.assertEqual(audit.new_value['quantity'], '150.0')
        self.assertEqual(audit.change_reason, "Corrected diesel fuel delivery amount based on invoice.")

    def test_audit_trail_stack_inference(self):
        record = EmissionRecord.objects.create(
            organization=self.org,
            scope_category=ScopeCategory.SCOPE1,
            activity_type="Fuel - Diesel",
            quantity=Decimal('100.0'),
            unit="L",
            normalized_quantity=Decimal('100.0'),
            normalized_unit="L",
            emission_factor=Decimal('2.68'),
            calculated_emission=Decimal('0.268'),
            suspicious_flag=False,
            approval_status=ApprovalStatus.PENDING,
            locked_for_audit=False
        )
        
        # Save change directly without setting attributes (simulating shell/migration update)
        record.quantity = Decimal('120.0')
        record.save()
        
        audit = AuditLog.objects.filter(emission_record=record).first()
        self.assertIsNotNone(audit)
        self.assertIn(audit.changed_by, ['shell_operator', 'system_operator'])
        self.assertIsNotNone(audit.change_reason)



    def test_date_parsing_and_preservation(self):
        from apps.ingestion.services import process_single_raw_record
        
        # 1. SAP posting date
        raw_sap = RawRecord.objects.create(
            datasource=self.datasource_sap,
            raw_json={
                'Material': 'Diesel', 
                'Fuel Quantity': '100', 
                'Fuel Unit': 'L',
                'Posting Date': '10.05.2026'
            },
            processing_status='UNPROCESSED'
        )
        process_single_raw_record(raw_sap)
        em_sap = EmissionRecord.objects.get(raw_record=raw_sap)
        self.assertEqual(str(em_sap.activity_date), '2026-05-10')

        # 2. Utility billing start/end and activity date
        raw_utility = RawRecord.objects.create(
            datasource=self.datasource_utility,
            raw_json={
                'Meter ID': 'MTR-TEST-99', 
                'Usage': '500', 
                'Unit': 'kWh', 
                'Tariff': 'Grid',
                'Billing Start': '2026-03-15',
                'Billing End': '2026-04-14'
            },
            processing_status='UNPROCESSED'
        )
        process_single_raw_record(raw_utility)
        em_utility = EmissionRecord.objects.get(raw_record=raw_utility)
        self.assertEqual(str(em_utility.billing_period_start), '2026-03-15')
        self.assertEqual(str(em_utility.billing_period_end), '2026-04-14')
        self.assertEqual(str(em_utility.activity_date), '2026-04-14')

        # 3. Travel date
        raw_travel = RawRecord.objects.create(
            datasource=self.datasource_travel,
            raw_json={
                'Employee ID': 'EMP-01', 
                'Flight Type': 'Domestic', 
                'From Airport': 'JFK', 
                'To Airport': 'LAX',
                'Distance': '1000',
                'Travel Date': '18.05.2026'
            },
            processing_status='UNPROCESSED'
        )
        process_single_raw_record(raw_travel)
        em_travel = EmissionRecord.objects.get(raw_record=raw_travel)
        self.assertEqual(str(em_travel.activity_date), '2026-05-18')

    def test_model_level_audit_lock(self):
        from django.core.exceptions import ValidationError
        
        # 1. Create a locked record
        record = EmissionRecord.objects.create(
            organization=self.org,
            scope_category=ScopeCategory.SCOPE1,
            activity_type="Fuel - Diesel",
            quantity=Decimal('100.0'),
            unit="L",
            normalized_quantity=Decimal('100.0'),
            normalized_unit="L",
            emission_factor=Decimal('2.68'),
            calculated_emission=Decimal('0.268'),
            suspicious_flag=False,
            approval_status=ApprovalStatus.APPROVED,
            locked_for_audit=True
        )

        # 2. Attempting to modify any field on a record that is already locked in DB should raise ValidationError
        record.quantity = Decimal('200.0')
        with self.assertRaises(ValidationError):
            record.save()
            
        # 3. Attempting to delete a locked record should also raise ValidationError
        with self.assertRaises(ValidationError):
            record.delete()

    def test_batch_approval_endpoint(self):
        # 1. Create two pending records
        record1 = EmissionRecord.objects.create(
            organization=self.org,
            scope_category=ScopeCategory.SCOPE1,
            activity_type="Fuel - Petrol",
            quantity=Decimal('50.0'),
            unit="L",
            normalized_quantity=Decimal('50.0'),
            normalized_unit="L",
            emission_factor=Decimal('2.31'),
            calculated_emission=Decimal('0.1155'),
            approval_status=ApprovalStatus.PENDING,
            locked_for_audit=False
        )
        record2 = EmissionRecord.objects.create(
            organization=self.org,
            scope_category=ScopeCategory.SCOPE2,
            activity_type="Electricity - Peak",
            quantity=Decimal('200.0'),
            unit="kWh",
            normalized_quantity=Decimal('200.0'),
            normalized_unit="kWh",
            emission_factor=Decimal('0.45'),
            calculated_emission=Decimal('0.09'),
            approval_status=ApprovalStatus.PENDING,
            locked_for_audit=False
        )

        # 2. Create another tenant and its record
        other_org = Organization.objects.create(name="Other Tenant")
        other_record = EmissionRecord.objects.create(
            organization=other_org,
            scope_category=ScopeCategory.SCOPE1,
            activity_type="Fuel - Petrol",
            quantity=Decimal('50.0'),
            unit="L",
            normalized_quantity=Decimal('50.0'),
            normalized_unit="L",
            emission_factor=Decimal('2.31'),
            calculated_emission=Decimal('0.1155'),
            approval_status=ApprovalStatus.PENDING,
            locked_for_audit=False
        )

        # 3. Call endpoint with self.client
        headers = {
            'HTTP_X_ORGANIZATION_ID': str(self.org.id)
        }
        
        payload = {
            "record_ids": [str(record1.id), str(record2.id), str(other_record.id)],
            "change_reason": "Approved during bulk verification"
        }
        
        response = self.client.post(
            '/api/emissions/approve_batch/',
            payload,
            content_type='application/json',
            **headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify that record1 and record2 are now APPROVED and locked
        record1.refresh_from_db()
        record2.refresh_from_db()
        other_record.refresh_from_db()
        
        self.assertEqual(record1.approval_status, ApprovalStatus.APPROVED)
        self.assertTrue(record1.locked_for_audit)
        self.assertEqual(record2.approval_status, ApprovalStatus.APPROVED)
        self.assertTrue(record2.locked_for_audit)
        
        # Verify cross-tenant record was NOT approved/locked
        self.assertEqual(other_record.approval_status, ApprovalStatus.PENDING)
        self.assertFalse(other_record.locked_for_audit)
        
        # Verify that AuditLogs were created for record1 and record2
        self.assertEqual(AuditLog.objects.filter(emission_record=record1).count(), 1)
        self.assertEqual(AuditLog.objects.filter(emission_record=record2).count(), 1)
        self.assertEqual(AuditLog.objects.filter(emission_record=other_record).count(), 0)
        
        # Check audit values
        audit = AuditLog.objects.filter(emission_record=record1).first()
        self.assertEqual(audit.change_reason, "Approved during bulk verification")
