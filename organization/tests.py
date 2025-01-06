from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from organization.models import Organization

class OrganizationTestCase(TestCase):
    def setUp(self):
        """
        Set up test data before each test runs.
        """
        self.user = User.objects.create_user(username='testuser', password='password')
        self.organization = Organization.objects.create(
            organization_name="Test Org",
            organization_pin="12345",
            organization_email="test@org.com",
            organization_phone="1234567890",
        )
        self.client.login(username='testuser', password='password')  # Authenticate user

    def test_create_organization(self):
        """
        Test creating an organization.
        """
        response = self.client.post(reverse('organization:organization_create'), {
            "organization_name": "New Org",
            "organization_pin": "67890",
            "organization_email": "new@org.com",
            "organization_phone": "0987654321",
        })
        self.assertEqual(response.status_code, 200)  # Expect success
        self.assertTrue(Organization.objects.filter(organization_name="New Org").exists())

    def test_get_organization_detail(self):
        """
        Test retrieving organization details.
        """
        response = self.client.get(reverse('organization:organization_detail', args=[self.organization.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Org")

    def test_update_organization(self):
        """
        Test updating organization details.
        """
        response = self.client.post(reverse('organization:organization_update', args=[self.organization.id]), {
            "organization_name": "Updated Org",
            "organization_pin": "54321",
            "organization_email": "updated@org.com",
            "organization_phone": "1112223333",
        })
        self.assertEqual(response.status_code, 200)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.organization_name, "Updated Org")

    def test_delete_organization(self):
        """
        Test deleting an organization.
        """
        response = self.client.post(reverse('organization:organization_delete', args=[self.organization.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())
