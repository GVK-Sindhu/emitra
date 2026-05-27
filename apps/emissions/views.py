from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.emissions.models import EmissionRecord, ApprovalStatus
from apps.emissions.serializers import EmissionRecordSerializer
from apps.organizations.utils import get_tenant_org
from apps.audits.models import AuditLog
from apps.ingestion.models import DataSource, IngestionStatus

class EmissionRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, editing, approving, and analyzing emissions data.
    Enforces multi-tenancy and produces strict audit logs on edits.
    """
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        org = get_tenant_org(self.request)
        queryset = EmissionRecord.objects.filter(organization=org)

        # Filters
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(raw_record__datasource__source_type=source)

        scope = self.request.query_params.get('scope')
        if scope:
            queryset = queryset.filter(scope_category=scope)

        suspicious_only = self.request.query_params.get('suspicious_only')
        if suspicious_only and suspicious_only.lower() == 'true':
            queryset = queryset.filter(suspicious_flag=True)

        approval_status = self.request.query_params.get('approval_status')
        if approval_status:
            queryset = queryset.filter(approval_status=approval_status)

        return queryset

    def perform_update(self, serializer):
        # 1. Extract audit parameters from request
        change_reason = self.request.data.get('change_reason', 'Updated by analyst')
        changed_by = self.request.data.get('changed_by', 'system_analyst')

        # 2. Attach audit parameters to the model instance being saved
        serializer.instance._changed_by = changed_by
        serializer.instance._change_reason = change_reason

        # 3. Save update (which runs recalculation logic inside the serializer and then the model save)
        serializer.save()

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk=None):
        """
        Approves an emission record, locking it from further changes for auditing.
        """
        record = self.get_object()
        if record.approval_status == ApprovalStatus.APPROVED:
            return Response({"detail": "Record is already approved."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Lock the record and set model-layer audit details
        record.approval_status = ApprovalStatus.APPROVED
        record.locked_for_audit = True
        record._changed_by = request.data.get('changed_by', 'system_analyst')
        record._change_reason = request.data.get('change_reason', 'Record approved and locked for audit.')
        record.save()
        
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk=None):
        """
        Rejects an emission record.
        """
        record = self.get_object()
        if record.locked_for_audit:
            return Response({"detail": "Cannot reject a locked record without admin intervention."}, status=status.HTTP_400_BAD_REQUEST)
            
        record.approval_status = ApprovalStatus.REJECTED
        record._changed_by = request.data.get('changed_by', 'system_analyst')
        record._change_reason = request.data.get('change_reason', 'Record rejected by analyst.')
        record.save()
        
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=False, methods=['POST'])
    def approve_batch(self, request):
        """
        Approves multiple emission records in batch, locking them for auditing.
        """
        record_ids = request.data.get('record_ids', [])
        if not record_ids:
            return Response({"detail": "No record IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        change_reason = request.data.get('change_reason', 'Batch approved and locked for audit.')
        changed_by = request.data.get('changed_by', 'system_analyst')
        
        # Enforce tenant isolation by filtering query to only tenant records
        org = get_tenant_org(self.request)
        records = EmissionRecord.objects.filter(id__in=record_ids, organization=org)
        
        if not records.exists():
            return Response({"detail": "No matching records found for this tenant."}, status=status.HTTP_404_NOT_FOUND)
            
        pending_records = [r for r in records if r.approval_status != ApprovalStatus.APPROVED]
        
        if not pending_records:
            return Response({"detail": "All selected records are already approved."}, status=status.HTTP_400_BAD_REQUEST)
            
        updated_records = []
        with transaction.atomic():
            for record in pending_records:
                record.approval_status = ApprovalStatus.APPROVED
                record.locked_for_audit = True
                record._changed_by = changed_by
                record._change_reason = change_reason
                record.save()
                updated_records.append(record)
                
        return Response({
            "detail": f"Successfully approved {len(updated_records)} records.",
            "approved_ids": [r.id for r in updated_records]
        })

    @action(detail=False, methods=['GET'])
    def dashboard_stats(self, request):
        """
        Gathers key counts for dashboard cards.
        """
        org = get_tenant_org(request)
        base_records = EmissionRecord.objects.filter(organization=org)
        
        total_records = base_records.count()
        suspicious_records = base_records.filter(suspicious_flag=True).count()
        approved_records = base_records.filter(approval_status=ApprovalStatus.APPROVED).count()
        
        # Failed imports are either failed raw records or failed file data sources
        failed_imports = DataSource.objects.filter(organization=org, ingestion_status=IngestionStatus.FAILED).count()
        
        return Response({
            "total_records": total_records,
            "suspicious_records": suspicious_records,
            "approved_records": approved_records,
            "failed_imports": failed_imports
        })
