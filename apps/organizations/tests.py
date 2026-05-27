from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.organizations.models import Organization

class OrganizationSecurityTests(APITestCase):
    
    def setUp(self):
        self.org_a = Organization.objects.create(name="Tenant A")
        self.org_b = Organization.objects.create(name="Tenant B")
        self.client_a = APIClient()
        self.client_a.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_a.id))

    def test_list_organizations_only_returns_own(self):
        # Querying list endpoint while context is set to Tenant A
        url = reverse('organization-list')
        response = self.client_a.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        
        # Verify only Tenant A is returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.org_a.id))
        self.assertEqual(results[0]['name'], "Tenant A")

    def test_retrieve_other_organization_returns_404(self):
        # Retrieve Tenant B details while context is Tenant A
        url = reverse('organization-detail', kwargs={'pk': self.org_b.id})
        response = self.client_a.get(url)
        
        # Since Tenant B is not in Tenant A's isolated queryset, it must return 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_own_organization_returns_200(self):
        # Retrieve Tenant A details while context is Tenant A
        url = reverse('organization-detail', kwargs={'pk': self.org_a.id})
        response = self.client_a.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Tenant A")
