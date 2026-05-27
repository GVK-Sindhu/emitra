from rest_framework import serializers
from decimal import Decimal
from apps.emissions.models import EmissionRecord, ScopeCategory, ApprovalStatus
from apps.emissions.services import (
    normalize_fuel_unit,
    normalize_electricity_unit,
    clean_decimal
)

class EmissionRecordSerializer(serializers.ModelSerializer):
    # Field to capture the analyst's justification for updates (used for AuditLog generation)
    change_reason = serializers.CharField(write_only=True, required=False, allow_blank=True)
    source_type = serializers.SerializerMethodField(read_only=True)
    raw_record_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'organization', 'raw_record', 'raw_record_data', 'source_type',
            'scope_category', 'activity_type',
            'quantity', 'unit', 'normalized_quantity', 'normalized_unit',
            'emission_factor', 'calculated_emission', 'suspicious_flag', 'suspicious_reason',
            'approval_status', 'locked_for_audit', 'created_at', 'updated_at',
            'change_reason', 'activity_date', 'billing_period_start', 'billing_period_end'
        ]
        read_only_fields = [
            'id', 'organization', 'raw_record', 'created_at', 'updated_at', 
            'locked_for_audit'
        ]

    def get_source_type(self, obj) -> str:
        if obj.raw_record and obj.raw_record.datasource:
            return obj.raw_record.datasource.source_type
        return "MANUAL"

    def get_raw_record_data(self, obj) -> dict:
        if obj.raw_record:
            return obj.raw_record.raw_json
        return {}

    def validate(self, attrs):
        # 1. Enforce audit locking
        if self.instance and self.instance.locked_for_audit:
            raise serializers.ValidationError("This record is locked for audit and cannot be modified.")
            
        # 2. Require change_reason if updating an existing record
        if self.instance and not attrs.get('change_reason'):
            raise serializers.ValidationError({"change_reason": "A reason is required to log this change."})
            
        return attrs

    def update(self, instance, validated_data):
        # Pop change reason so it doesn't get saved directly into the model
        change_reason = validated_data.pop('change_reason', '')
        
        # Get potential raw values to check if we should recalculate
        qty = validated_data.get('quantity', instance.quantity)
        unit = validated_data.get('unit', instance.unit)
        factor = validated_data.get('emission_factor', instance.emission_factor)
        
        # Determine source type to do proper unit normalization
        source_type = "MANUAL"
        if instance.raw_record and instance.raw_record.datasource:
            source_type = instance.raw_record.datasource.source_type

        # If quantity or unit changed and the user did not supply new normalized fields, recalculate
        if ('quantity' in validated_data or 'unit' in validated_data) and 'normalized_quantity' not in validated_data:
            if source_type == 'SAP':
                norm_qty, norm_unit = normalize_fuel_unit(Decimal(qty), unit)
                validated_data['normalized_quantity'] = norm_qty
                validated_data['normalized_unit'] = norm_unit
            elif source_type == 'UTILITY':
                norm_qty, norm_unit = normalize_electricity_unit(Decimal(qty), unit)
                validated_data['normalized_quantity'] = norm_qty
                validated_data['normalized_unit'] = norm_unit
            else:
                validated_data['normalized_quantity'] = Decimal(qty)
                validated_data['normalized_unit'] = unit

        # Recalculate emissions if quantity, unit, or factor changed, unless calculated_emission is explicitly provided
        if 'calculated_emission' not in validated_data:
            norm_qty = validated_data.get('normalized_quantity', instance.normalized_quantity)
            current_factor = validated_data.get('emission_factor', instance.emission_factor)
            
            # If Scope 3 travel, calculated_emission matches normalized_quantity / 1000
            # Otherwise normalized_quantity * emission_factor / 1000
            if instance.scope_category == ScopeCategory.SCOPE3 and source_type == 'TRAVEL':
                # Normalized qty for travel represents kg CO2e, so calculate in tCO2e
                validated_data['calculated_emission'] = Decimal(norm_qty) / Decimal('1000.0')
            else:
                validated_data['calculated_emission'] = (Decimal(norm_qty) * Decimal(current_factor)) / Decimal('1000.0')

        return super().update(instance, validated_data)
