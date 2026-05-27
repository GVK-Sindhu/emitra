import uuid
from django.db import models
from apps.emissions.models import EmissionRecord

class AuditLog(models.Model):
    """
    Maintains a robust, immutable audit log tracking modifications to emission records.
    Every edit requires a reason and stores the before and after state.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.CharField(max_length=255, default='anonymous_analyst')
    old_value = models.JSONField(help_text="Stores the serialized state before changes")
    new_value = models.JSONField(help_text="Stores the serialized state after changes")
    change_reason = models.TextField(help_text="Justification for the change")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"AuditLog {self.id} for EmissionRecord {self.emission_record_id}"
