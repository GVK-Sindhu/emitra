from rest_framework import viewsets
from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer
from apps.organizations.utils import get_tenant_org

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows organizations to be viewed or edited.
    Enforces strict multi-tenancy context.
    """
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        # Restrict queries to return only the active tenant organization context.
        # This prevents tenant enumeration and spoofing.
        org = get_tenant_org(self.request)
        return Organization.objects.filter(pk=org.pk)
