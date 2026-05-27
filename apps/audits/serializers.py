from rest_framework import serializers
from apps.audits.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'emission_record', 'changed_by', 'old_value', 'new_value', 'change_reason', 'timestamp']
        read_only_fields = ['id', 'timestamp']
