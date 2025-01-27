from django.test import TestCase
from organization.models import Organization
from customer.models import Customer
from transaction.models import Transaction
from django.contrib.auth.models import User


class TransactionModelTest(TestCase):
    def setUp(self):
        # Set up a user, organization, and customer
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

    def test_create_valid_transaction(self):
        """Test creating a valid Transaction record."""
        transaction = Transaction.objects.create(
            organization=self.organization,
            customer=self.customer,
            trader_invoice_number="INV123",
            receipt_number=1001,
            document_type="invoice",
            reason="sale",
        )
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.receipt_number, 1001)
        self.assertEqual(transaction.document_type, "invoice")

    def test_transaction_str_representation(self):
        """Test the string representation of a Transaction."""
        transaction = Transaction.objects.create(
            organization=self.organization,
            customer=self.customer,
            trader_invoice_number="INV123",
            receipt_number=1002,
            document_type="receipt",
            reason="purchase",
        )
        expected_str = f"Transaction 1002-receipt for {self.customer.customer_name} - purchase"
        self.assertEqual(str(transaction), expected_str)

    def test_unique_receipt_number(self):
        """Test that receipt_number must be unique."""
        Transaction.objects.create(
            organization=self.organization,
            customer=self.customer,
            trader_invoice_number="INV123",
            receipt_number=1003,
            document_type="invoice",
        )
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError
            Transaction.objects.create(
                organization=self.organization,
                customer=self.customer,
                trader_invoice_number="INV124",
                receipt_number=1003,  # Duplicate receipt_number
                document_type="credit_note",
            )

    def test_document_upload_path(self):
        """Test that the document_path is correctly set when a file is uploaded."""
        transaction = Transaction.objects.create(
            organization=self.organization,
            customer=self.customer,
            trader_invoice_number="INV126",
            receipt_number=1005,
            document_type="invoice",
            document_path="transaction_documents/sample_receipt.pdf",
        )
        self.assertEqual(transaction.document_path, "transaction_documents/sample_receipt.pdf")
