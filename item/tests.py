from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError
from organization.models import Organization
from item.models import Item
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from item.signals import track_item_creation


class ItemModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect the signal before running tests
        post_save.disconnect(track_item_creation, sender=Item)

    @classmethod
    def tearDownClass(cls):
        # Reconnect the signal after tests are done
        post_save.connect(track_item_creation, sender=Item)
        super().tearDownClass()

    def setUp(self):
        # Create a user and an organization
        self.user = User.objects.create_user(
            username="testuser", password="testpass")
        self.organization = Organization.objects.create(
            organization_name="TestOrg",
            organization_pin="ORG123",
            organization_email="org@test.com",
            organization_physical_address="123 Test St",
            organization_phone="0700000000",
        )
        self.organization.user.add(self.user)

    def test_create_item_with_valid_data(self):
        """Test creating an item with valid data."""
        item = Item.objects.create(
            organization=self.organization,
            item_name="Test Item",
            origin_nation_code="KE",
            item_type_code="01",
            quantity_unit_code="KG",
            package_unit_code="BOX",
            item_class_code="123",
            item_tax_code="A",
            item_opening_balance=100.00,
            item_current_balance=100.00,
        )
        self.assertIsNotNone(
            item.itemCd, "Item code should be auto-generated.")
        self.assertEqual(item.item_name, "Test Item")

    def test_unique_together_organization_itemCd(self):
        """Test the unique constraint for organization and itemCd."""
        Item.objects.create(
            organization=self.organization,
            item_name="Item 1",
            origin_nation_code="KE",
            item_type_code="01",
            quantity_unit_code="KG",
            package_unit_code="BOX",
            item_class_code="123",
            item_tax_code="A",
            itemCd="ITEM001",
        )
        with self.assertRaises(IntegrityError):
            Item.objects.create(
                organization=self.organization,
                item_name="Item 2",  # Different name
                origin_nation_code="KE",
                item_type_code="01",
                quantity_unit_code="KG",
                package_unit_code="BOX",
                item_class_code="123",
                item_tax_code="A",
                itemCd="ITEM001",  # Duplicate itemCd
            )

    def test_unique_together_organization_item_name(self):
        """Test the unique constraint for organization and item_name."""
        Item.objects.create(
            organization=self.organization,
            item_name="Item 1",
            origin_nation_code="KE",
            item_type_code="01",
            quantity_unit_code="KG",
            package_unit_code="BOX",
            item_class_code="123",
            item_tax_code="A",
            itemCd="ITEM001",
        )
        with self.assertRaises(IntegrityError):
            Item.objects.create(
                organization=self.organization,
                item_name="Item 1",  # Duplicate name
                origin_nation_code="KE",
                item_type_code="01",
                quantity_unit_code="KG",
                package_unit_code="BOX",
                item_class_code="123",
                item_tax_code="A",
                itemCd="ITEM002",  # Different itemCd
            )