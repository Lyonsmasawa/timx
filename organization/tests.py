# organization/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Organization

User = get_user_model()

class OrganizationModelTest(TestCase):
    def setUp(self):
        # Create a user to attach to the Organizations (since it's a ManyToMany)
        self.user = User.objects.create_user(username='orguser', password='testpass')

    def test_create_organization(self):
        """
        Ensure that an organization can be created and saved to the database.
        """
        org = Organization.objects.create(
            organization_name="MyOrg",
            organization_pin="ORG-123",
            organization_email="org@example.com",
            organization_physical_address="123 Main St",
            organization_phone="555-1234",
        )
        
        # add the user to the ManyToMany field separately
        org.user.add(self.user)

        self.assertEqual(Organization.objects.count(), 1)
        saved_org = Organization.objects.first()
        self.assertEqual(saved_org.organization_name, "MyOrg")
        self.assertEqual(saved_org.organization_pin, "ORG-123")

        # Check ManyToMany relationship
        self.assertIn(self.user, saved_org.user.all())

    def test_unique_name_and_pin(self):
        """
        organization_name and organization_pin are unique. Attempting to create duplicates should raise an error.
        """
        Organization.objects.create(
            organization_name="UniqueOrg",
            organization_pin="PIN-001",
            organization_email="unique@example.com",
            organization_physical_address="111 Street",
            organization_phone="111-1111",
        )

        with self.assertRaises(Exception):
            # Could be IntegrityError or Django ValidationError, 
            # depending on how you handle it. We'll catch a generic Exception for demonstration.
            Organization.objects.create(
                organization_name="UniqueOrg",
                organization_pin="PIN-001",
                organization_email="duplicate@example.com",
                organization_physical_address="222 Street",
                organization_phone="222-2222",
            )

    def test_prevent_pin_edit_after_creation(self):
        """
        The model's save() raises a ValueError if we try to change organization_pin after creation.
        """
        org = Organization.objects.create(
            organization_name="NoPinChange",
            organization_pin="ORIG-PIN",
            organization_email="pinchange@example.com",
            organization_physical_address="Some Address",
            organization_phone="1234",
        )

        # Attempt to change the pin
        org.organization_pin = "NEW-PIN"
        with self.assertRaises(ValueError) as ctx:
            org.save()

        self.assertIn("Organization PIN cannot be edited.", str(ctx.exception))
