from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.ingestion.models import DataSource, RawRecord
from apps.ingestion.serializers import DataSourceSerializer, RawRecordSerializer
from apps.organizations.utils import get_tenant_org
from apps.ingestion.services import ingest_data_source

class DataSourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint to list uploads and upload new CSV sources.
    Ingestion is run synchronously for the MVP to prevent background queue dependencies.
    """
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        # Enforce multi-tenancy filter
        org = get_tenant_org(self.request)
        return DataSource.objects.filter(organization=org)

    def perform_create(self, serializer):
        org = get_tenant_org(self.request)
        # Associate user uploading if provided, default to 'system_user'
        uploaded_by = self.request.data.get('uploaded_by', 'system_user')
        datasource = serializer.save(organization=org, uploaded_by=uploaded_by)
        
        # Trigger ingestion synchronously
        ingest_data_source(datasource.id)

class RawRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view raw database records before normalization.
    """
    serializer_class = RawRecordSerializer

    def get_queryset(self):
        org = get_tenant_org(self.request)
        return RawRecord.objects.filter(datasource__organization=org)
