from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Organization
from item.models import Item
from customer.models import Customer
from transaction.models import Transaction

class OrganizationViewsTestCase(TestCase):
    
    def setUp(self):
        # Set up a user and login
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
    
    def test_organization_create(self):
        # Test that a new organization can be created
        url = reverse('organization:organization_create')
        data = {
            user: user
            'organization_name': 'Test Organization',
            'organization_email': 'testorg@example.com',
            'organization_phone': '1234567890',
            'organization_physical_address': '123 Test St',
            'organization_pin': '12345',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Form should be valid
        self.assertContains(response, "Organization created successfully!")
        
        # Verify the new organization is in the database
        organization = Organization.objects.first()
        self.assertEqual(organization.organization_name, 'Test Organization')
        
    

