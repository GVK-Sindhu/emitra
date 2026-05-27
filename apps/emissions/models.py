import uuid
from django.db import models
from django.core.exceptions import ValidationError
from apps.organizations.models import Organization
from apps.ingestion.models import RawRecord

class ScopeCategory(models.TextChoices):
    SCOPE1 = 'Scope1', 'Scope 1 - Direct Emissions'
    SCOPE2 = 'Scope2', 'Scope 2 - Indirect Emissions (Electricity)'
    SCOPE3 = 'Scope3', 'Scope 3 - Value Chain (Business Travel)'

class ApprovalStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class EmissionRecord(models.Model):
    """
    Stores normalized, validated, and audited ESG activity and calculated emissions data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='emission_records')
    raw_record = models.ForeignKey(
        RawRecord, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='normalized_records'
    )
    scope_category = models.CharField(max_length=50, choices=ScopeCategory.choices)
    activity_type = models.CharField(max_length=100)
    
    # Original raw data
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=50)

    # Standardized/Normalized data
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    normalized_unit = models.CharField(max_length=50)

    # Calculated metrics
    emission_factor = models.DecimalField(max_digits=12, decimal_places=6)
    # calculated_emission represents Metric Tons CO2e (tCO2e)
    calculated_emission = models.DecimalField(max_digits=18, decimal_places=6)

    # Auditing / Verification
    suspicious_flag = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True, null=True)
    approval_status = models.CharField(
        max_length=50, 
        choices=ApprovalStatus.choices, 
        default=ApprovalStatus.PENDING
    )
    locked_for_audit = models.BooleanField(default=False)
    
    # Compliance & Business Activity Timeline
    activity_date = models.DateField(null=True, blank=True, db_index=True)
    billing_period_start = models.DateField(null=True, blank=True)
    billing_period_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emission_records'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scope_category} - {self.activity_type} ({self.calculated_emission} tCO2e)"

    def _serialize_state(self) -> dict:
        return {
            'scope_category': self.scope_category,
            'activity_type': self.activity_type,
            'quantity': str(self.quantity) if self.quantity is not None else '0.0',
            'unit': self.unit,
            'normalized_quantity': str(self.normalized_quantity) if self.normalized_quantity is not None else '0.0',
            'normalized_unit': self.normalized_unit,
            'emission_factor': str(self.emission_factor) if self.emission_factor is not None else '0.0',
            'calculated_emission': str(self.calculated_emission) if self.calculated_emission is not None else '0.0',
            'suspicious_flag': self.suspicious_flag,
            'suspicious_reason': self.suspicious_reason,
            'approval_status': self.approval_status,
            'locked_for_audit': self.locked_for_audit
        }

    def save(self, *args, **kwargs):
        is_update = False
        original_serialized = None
        
        if self.pk:
            try:
                # Check the database state before saving updates
                original = EmissionRecord.objects.get(pk=self.pk)
                if original.locked_for_audit:
                    raise ValidationError("This record is locked for audit and cannot be modified.")
                is_update = True
                original_serialized = original._serialize_state()
            except EmissionRecord.DoesNotExist:
                # Record is being created for the first time
                pass
                
        super().save(*args, **kwargs)
        
        if is_update:
            current_serialized = self._serialize_state()
            # Compare state fields
            changed = any(original_serialized[k] != current_serialized[k] for k in original_serialized)
            if changed:
                changed_by = getattr(self, '_changed_by', None)
                change_reason = getattr(self, '_change_reason', None)
                
                if not changed_by or not change_reason:
                    import inspect
                    frame_records = inspect.stack()
                    is_admin = any('django/contrib/admin' in f.filename for f in frame_records)
                    is_shell = any('django/core/management' in f.filename or 'ipython' in f.filename or 'manage.py' in f.filename for f in frame_records)
                    
                    if is_admin:
                        changed_by = changed_by or 'admin_portal'
                        change_reason = change_reason or 'Record modified via Django Administrative Portal.'
                    elif is_shell:
                        changed_by = changed_by or 'shell_operator'
                        change_reason = change_reason or 'Record updated via management script / interactive shell.'
                    else:
                        changed_by = changed_by or 'system_operator'
                        change_reason = change_reason or 'Automated database correction / update.'
                
                # Import locally to prevent circular dependencies
                from apps.audits.models import AuditLog
                AuditLog.objects.create(
                    emission_record=self,
                    changed_by=changed_by,
                    old_value=original_serialized,
                    new_value=current_serialized,
                    change_reason=change_reason
                )

    def delete(self, *args, **kwargs):
        if self.locked_for_audit:
            raise ValidationError("This record is locked for audit and cannot be deleted.")
        super().delete(*args, **kwargs)
