from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.organizations.views import OrganizationViewSet
from apps.ingestion.views import DataSourceViewSet, RawRecordViewSet
from apps.emissions.views import EmissionRecordViewSet
from apps.audits.views import AuditLogViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'datasources', DataSourceViewSet, basename='datasource')
router.register(r'rawrecords', RawRecordViewSet, basename='rawrecord')
router.register(r'emissions', EmissionRecordViewSet, basename='emissionrecord')
router.register(r'audits', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
]
