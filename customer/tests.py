from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from organization.models import Organization
from django.contrib.auth.models import User
from customer.models import Customer
from django.db.models.signals import post_save
from customer.signals import track_customer_creation

class CustomerModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect the signal before running tests
        post_save.disconnect(track_customer_creation, sender=Customer)

    @classmethod
    def tearDownClass(cls):
        # Reconnect the signal after tests are done
        post_save.connect(track_customer_creation, sender=Customer)
        super().tearDownClass()

    def setUp(self):
        # Set up a user and an organization
        self.user = User.objects.create_user(
            username="testuser", password="testpass")
        self.organization = Organization.objects.create(
            organization_name="TestOrg",
            organization_pin="ORG123456",
            organization_email="org@test.com",
            organization_physical_address="123 Test St",
            organization_phone="555-1234",
        )
        self.organization.user.add(self.user)

    def test_create_customer_valid(self):
        """Test that a valid Customer is created successfully."""
        customer = Customer.objects.create(
            organization=self.organization,
            customer_name="John Doe",
            customer_pin="CUST12345",
            customer_address="456 Customer St",
            customer_phone="555-6789",
            customer_email="johndoe@test.com",
        )
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.customer_name, "John Doe")

    def test_unique_customer_pin(self):
        """Test that customer_pin is unique globally."""
        Customer.objects.create(
            organization=self.organization,
            customer_name="John Doe",
            customer_pin="CUST12345",
            customer_address="456 Customer St",
            customer_phone="555-6789",
            customer_email="johndoe@test.com",
        )
        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                organization=self.organization,
                customer_name="Jane Smith",
                customer_pin="CUST12345",
                customer_address="789 Another St",
                customer_phone="555-9876",
                customer_email="janesmith@test.com",
            )

    def test_unique_email_within_organization(self):
        """Test that customer_email is unique within an organization."""
        Customer.objects.create(
            organization=self.organization,
            customer_name="John Doe",
            customer_pin="CUST12345",
            customer_address="456 Customer St",
            customer_phone="555-6789",
            customer_email="johndoe@test.com",
        )
        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                organization=self.organization,
                customer_name="Jane Smith",
                customer_pin="CUST67890",
                customer_address="789 Another St",
                customer_phone="555-9876",
                customer_email="johnde@test.com",  # Same email within the same org
            )

    def test_unique_phone_within_organization(self):
        """Test that customer_phone is unique within an organization."""
        Customer.objects.create(
            organization=self.organization,
            customer_name="John Doe",
            customer_pin="CUST12345",
            customer_address="456 Customer St",
            customer_phone="555-6789",
            customer_email="johndoe@test.com",
        )
        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                organization=self.organization,
                customer_name="Jane Smith",
                customer_pin="CUST67890",
                customer_address="789 Another St",
                customer_phone="555-6789",  # Same phone within the same org
                customer_email="janesmith@test.com",
            )

    def test_min_length_validator_on_customer_pin(self):
        """Test that customer_pin respects the MinLengthValidator."""
        customer = Customer(
            organization=self.organization,
            customer_name="Short Pin",
            customer_pin="CUST12",  # Too short
            customer_address="123 Short St",
            customer_phone="555-1234",
            customer_email="shortpin@test.com",
        )
        with self.assertRaises(ValidationError):
            customer.full_clean()  # Triggers model validation
