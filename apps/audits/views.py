from rest_framework import viewsets
from apps.audits.models import AuditLog
from apps.audits.serializers import AuditLogSerializer
from apps.organizations.utils import get_tenant_org

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows audit logs to be viewed.
    """
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        org = get_tenant_org(self.request)
        queryset = AuditLog.objects.filter(emission_record__organization=org)
        
        emission_record_id = self.request.query_params.get('emission_record')
        if emission_record_id:
            queryset = queryset.filter(emission_record_id=emission_record_id)
            
        return queryset
