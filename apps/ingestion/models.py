import uuid
from django.db import models
from apps.organizations.models import Organization

class SourceType(models.TextChoices):
    SAP = 'SAP', 'SAP Fuel/Procurement Export'
    UTILITY = 'UTILITY', 'Utility Electricity Export'
    TRAVEL = 'TRAVEL', 'Corporate Travel Export'

class IngestionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Processing'
    PROCESSING = 'PROCESSING', 'Processing File'
    SUCCESS = 'SUCCESS', 'Ingested Successfully'
    FAILED = 'FAILED', 'Ingestion Failed'

class ProcessingStatus(models.TextChoices):
    UNPROCESSED = 'UNPROCESSED', 'Unprocessed'
    SUCCESS = 'SUCCESS', 'Successfully Normalized'
    SUSPICIOUS = 'SUSPICIOUS', 'Normalized with Suspicious Flags'
    FAILED = 'FAILED', 'Normalization Failed'

class DataSource(models.Model):
    """
    Tracks uploaded raw CSV export files and the progress of their digestion.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='data_sources')
    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    uploaded_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_by = models.CharField(max_length=255, default='system_user')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ingestion_status = models.CharField(
        max_length=50, 
        choices=IngestionStatus.choices, 
        default=IngestionStatus.PENDING
    )
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'data_sources'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.source_type} upload ({self.id}) - {self.ingestion_status}"

class RawRecord(models.Model):
    """
    Preserves the raw imported row as an immutable source of truth before normalization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='raw_records')
    raw_json = models.JSONField(help_text="Stores the exact raw row columns parsed from CSV")
    processing_status = models.CharField(
        max_length=50, 
        choices=ProcessingStatus.choices, 
        default=ProcessingStatus.UNPROCESSED
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'raw_records'

    def __str__(self):
        return f"RawRecord {self.id} (Status: {self.processing_status})"
