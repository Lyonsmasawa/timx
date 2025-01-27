from django.test import TestCase
from django.urls import reverse
from item.models import Item
from item_movement.models import ItemMovement
from organization.models import Organization
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from item_movement.signals import track_stock_movement


class ItemMovementModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect the signal before running tests
        post_save.disconnect(track_stock_movement, sender=Item)

    @classmethod
    def tearDownClass(cls):
        # Reconnect the signal after tests are done
        post_save.connect(track_stock_movement, sender=Item)
        super().tearDownClass()

    def setUp(self):
        # Create user, organization, and item for tests
        self.user = User.objects.create_user(
            username="testuser", password="testpass")
        self.organization = Organization.objects.create(
            organization_name="TestOrg",
            organization_pin="ORG123",
            organization_email="org@test.com",
            organization_physical_address="123 Test St",
            organization_phone="555-1234",
        )
        self.item = Item.objects.create(
            organization=self.organization,
            item_name="Test Item",
            origin_nation_code="KE",
            item_type_code="01",
            quantity_unit_code="KG",
            package_unit_code="BOX",
            item_class_code="123",
            item_tax_code="A",
            item_opening_balance=100.0,
            item_current_balance=100.0,
            itemCd="ITEM001",
        )

    def test_create_item_movement(self):
        """Test creating a valid ItemMovement record."""
        movement = ItemMovement.objects.create(
            item=self.item,
            movement_type="ADD",
            movement_reason="Restocking",
            item_unit=50.0,
        )
        self.assertEqual(ItemMovement.objects.count(), 1)
        self.assertEqual(movement.item, self.item)
        self.assertEqual(movement.movement_type, "ADD")
        self.assertEqual(float(movement.item_unit), 50.00)

    def test_item_movement_str_representation(self):
        """Test the string representation of an ItemMovement."""
        movement = ItemMovement.objects.create(
            item=self.item,
            movement_type="REMOVE",
            movement_reason="Sale",
            item_unit=10.0,
        )
        self.assertEqual(
            str(movement),
            f"REMOVE - {self.item.item_name} - Sale (10.0)"
        )
