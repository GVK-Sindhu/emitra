from rest_framework import serializers
from apps.ingestion.models import DataSource, RawRecord

class DataSourceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'organization', 'organization_name', 'source_type', 
            'uploaded_file', 'uploaded_by', 'uploaded_at', 
            'ingestion_status', 'error_message'
        ]
        read_only_fields = ['id', 'organization', 'organization_name', 'uploaded_at', 'ingestion_status', 'error_message']

class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'datasource', 'raw_json', 'processing_status', 'error_message', 'created_at']
        read_only_fields = ['id', 'created_at']
