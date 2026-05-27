from rest_framework.exceptions import ValidationError
from apps.organizations.models import Organization

def get_tenant_org(request) -> Organization:
    """
    Determines the current tenant organization based on request header.
    If header X-Organization-ID is missing or invalid, raises ValidationError.
    This pattern ensures strict data isolation.
    """
    org_id = request.headers.get('X-Organization-ID')
    if not org_id:
        raise ValidationError("Organization header 'X-Organization-ID' is required.")
        
    try:
        return Organization.objects.get(pk=org_id)
    except (Organization.DoesNotExist, ValueError):
        raise ValidationError("Invalid or unmapped tenant organization.")
