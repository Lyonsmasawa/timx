from django.test import TestCase
from transaction.models import Transaction
from item.models import Item
from sales_items.models import SalesItems
from organization.models import Organization
from customer.models import Customer
from django.contrib.auth.models import User


class SalesItemsModelTest(TestCase):
    def setUp(self):
        # Set up a user, organization, item, customer, and transaction for testing
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.organization = Organization.objects.create(
            organization_name="TestOrg",
            organization_pin="ORG123",
            organization_email="org@test.com",
            organization_physical_address="123 Test St",
            organization_phone="555-1234",
        )
        self.customer = Customer.objects.create(
            organization=self.organization,
            customer_name="John Doe",
            customer_pin="CUST12345",
            customer_address="456 Customer St",
            customer_phone="555-6789",
            customer_email="johndoe@test.com",
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
            item_opening_balance=100.00,
            item_current_balance=100.00,
            itemCd="ITEM001",
        )
        self.transaction = Transaction.objects.create(
            organization=self.organization,
            customer=self.customer,
            trader_invoice_number="INV123",
            receipt_number=1001,
            document_type="invoice",
            reason="sale",
        )

    def test_create_sales_item_valid(self):
        """Test creating a valid SalesItems record."""
        sales_item = SalesItems.objects.create(
            transaction=self.transaction,
            item=self.item,
            item_description="Test Item Description",
            qty=10.00,
            rate=50.00,
            discount_rate=10.00,  # 10% discount
            discount_amount=50.00,  # Pre-calculated (10% of 500)
            tax_code="VAT",
            line_total=450.00,  # After discount
        )
        self.assertEqual(SalesItems.objects.count(), 1)
        self.assertEqual(sales_item.item_description, "Test Item Description")
        self.assertEqual(float(sales_item.line_total), 450.00)

    def test_sales_item_str_representation(self):
        """Test the string representation of SalesItems."""
        sales_item = SalesItems.objects.create(
            transaction=self.transaction,
            item=self.item,
            item_description="Sample Item Description",
            qty=5.00,
            rate=100.00,
            discount_rate=0.00,
            discount_amount=0.00,
            tax_code="VAT",
            line_total=500.00,
        )
        self.assertEqual(str(sales_item), "Sales Item: Sample Item Description")
