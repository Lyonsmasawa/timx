from django.db import models
from commons.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User


class Item(BaseModel):
    # Example choices
    COUNTRY_CHOICES = [
        ('KE', 'Kenya'),
        ('US', 'United States'),
        ("AC", "ASCENSION ISLAND"),
        ("AD", "ANDOKRA"),
        ("AE", "UNITED ARAB EMIRATES"),
        ("AG", "ANTIGUA AND BARBUDA"),
        ("AI", "ANGUILLA"),
        ("AL", "ALBANIA"),
        ("AM", "ARMENIA"),
        ("AN", "NETHERLANDS ANTILLES"),
        ("AO", "ANGOLA"),
        ("AQ", "ANTARCTICA"),
        ("AR", "ARGENTINA"),
        ("AS", "AMERICAN SAMOA"),
        ("AT", "AUSTRIA"),
        ("AU", "AUSTRALIA"),
        ("AW", "ARUBA"),
        ("AX", "ALAND ISLANDS"),
    ]

    TAX_TYPE_CHOICES = [
        ("A", "A-Exempt"),
        ("B", "B-16.00%"),
        ("C", "C-0%"),
        ("D", "D-Non-VAT"),
        ("E", "E-8%"),
    ]

    TAXPAYER_STATUS_CHOICES = [
        ("A", "Active"),
        ("D", "Inactive"),
    ]

    PRODUCT_TYPE_CHOICES = [
        ("1", "Raw Material"),
        ("2", "Finished Product"),
        ("3", "Service without stock"),
    ]

    UNIT_CHOICES = [
        ('NT', 'NET'),
        ('KG', 'Kilogram'),
    ]

    PACKAGE_CHOICES = [
        ('AM', 'Ampoule'),
        ('BA', 'Barrel'),
        ('BC', 'Bottlecrate'),
        ('BE', 'Bundle'),
        ('BF', 'Balloon, non-protected'),
        ('BG', 'Bag'),
        ('BJ', 'Bucket'),
        ('BK', 'Basket'),
        ('BL', 'Bale'),
        ('BQ', 'Bottle, protected cylindrical'),
        ('BR', 'Bar'),
        ('BV', 'Bottle, bulbous'),
        ('BZ', 'Bag'),
        ('CA', 'Can'),
        ('CH', 'Chest'),
        ('CJ', 'Coffin'),
        ('CL', 'Coil'),
        ('CR', 'Wooden Box, Wooden Case'),
        ('CS', 'Cassette'),
        ('CT', 'Carton'),
        ('CTN', 'Container'),
        ('CY', 'Cylinder'),
        ('DR', 'Drum'),
        ('GT', 'Extra Countable Item'),
        ('HH', 'Hand Baggage'),
        ('IZ', 'Ingots'),
        ('JR', 'Jar'),
        ('JU', 'Jug'),
        ('JY', 'Jerry Can Cylindrical'),
        ('KZ', 'Canister'),
        ('LZ', 'Logs, in bundle/bunch/truss'),
        ('NT', 'Net'),
        ('OU', 'Non-Exterior Packaging Unit'),
        ('PD', 'Poddon'),
        ('PG', 'Plate'),
        ('PI', 'Pipe'),
        ('PO', 'Pilot'),
        ('PU', 'Traypack'),
        ('RL', 'Reel'),
        ('RO', 'Roll'),
        ('RZ', 'Rods, in bundle/bunch/truss'),
        ('SK', 'Skeletoncase'),
        ('TY', 'Tank, cylindrical'),
        ('VG', 'Bulk, gas (at 1031 mbar 15°C)'),
        ('VL', 'Bulk, liquid (at normal temperature/pressure)'),
        ('VO', 'Bulk, solid, large particles ("nodules")'),
        ('VQ', 'Bulk, gas (liquefied at abnormal temperature/pressure)'),
        ('VR', 'Bulk, solid, granular particles ("grains")'),
        ('VT', 'Extra Bulk Item'),
        ('VY', 'Bulk, fine particles ("powder")'),
        ('ML', 'Mills cigarette'),
        ('TN', 'TAN 1 TAN (Refer to 20 Bags)')
    ]

    UNIT_CHOICES = [
        ('4B', 'Pair'),
        ('AV', 'Cap'),
        ('BA', 'Barrel'),
        ('BE', 'Bundle'),
        ('BG', 'Bag'),
        ('BL', 'Block'),
        ('BLL', 'Barrel (petroleum)'),
        ('BX', 'Box'),
        ('CA', 'Can'),
        ('CEL', 'Cell'),
        ('CMT', 'Centimetre'),
        ('CR', 'Carat'),
        ('DR', 'Drum'),
        ('DZ', 'Dozen'),
        ('GLL', 'Gallon'),
        ('GRM', 'Gram'),
        ('GRO', 'Gross'),
        ('KG', 'Kilogram'),
        ('KTM', 'Kilometre'),
        ('KWT', 'Kilowatt'),
        ('L', 'Litre'),
        ('LBR', 'Pound'),
        ('LK', 'Link'),
        ('LTR', 'Litre'),
        ('M', 'Metre'),
        ('M2', 'Square Metre'),
        ('M3', 'Cubic Metre'),
        ('MGM', 'Milligram'),
        ('MTR', 'Metre'),
        ('MWT', 'Megawatt hour (1000 kW.h)'),
        ('NO', 'Number'),
        ('NX', 'Part per thousand'),
        ('PA', 'Packet'),
        ('PG', 'Plate'),
        ('PR', 'Pair'),
        ('RL', 'Reel'),
        ('RO', 'Roll'),
        ('SET', 'Set'),
        ('ST', 'Sheet'),
        ('TNE', 'Tonne (metric ton)'),
        ('TU', 'Tube'),
        ('U', 'Pieces/Item'),
        ('YRD', 'Yard')
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    origin_nation_code = models.CharField(
        max_length=2, choices=COUNTRY_CHOICES)
    item_type_code = models.CharField(
        max_length=2, choices=PRODUCT_TYPE_CHOICES)
    quantity_unit_code = models.CharField(
        max_length=3,
        choices=UNIT_CHOICES,
    )
    package_unit_code = models.CharField(
        max_length=3,
        choices=PACKAGE_CHOICES,
    )
    item_class_code = models.CharField(max_length=2, choices=TAX_TYPE_CHOICES)
    item_tax_code = models.CharField(
        max_length=1, choices=TAXPAYER_STATUS_CHOICES)
    item_opening_balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    item_current_balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    item_system_id = models.CharField(max_length=200, blank=True, null=True)
    item_system_name = models.CharField(max_length=200, blank=True, null=True)
    itemCd = models.CharField(max_length=16, unique=True)

    def generate_item_cd(self):
        # Country code (e.g., KE for Kenya)
        country_code = self.origin_nation_code
        # Product type (e.g., 2 for Finished Product)
        product_type = self.item_type_code
        # Packaging unit (e.g., NT for NET)
        package_unit = self.package_unit_code
        # Quantity unit (e.g., BA for Barrel)
        quantity_unit = self.quantity_unit_code
        # Increment logic (e.g., 0000012 for item number)
        last_item = Item.objects.filter(
            itemCd__startswith=f"{country_code}{product_type}{package_unit}{quantity_unit}").order_by('-itemCd').first()
        last_number = int(last_item.itemCd[-7:]) if last_item else 0
        next_number = last_number + 1
        increment = f"{next_number:07d}"

        return f"{country_code}{product_type}{package_unit}{quantity_unit}{increment}"

    def __str__(self):
        return self.item_name

    def save(self, *args, **kwargs):
        if not self.itemCd:
            # Generate itemCd based on the required format
            self.itemCd = self.generate_item_cd()

        if not self.key:
            # Generate the key unique to the user's organizations
            self.key = self.generate_unique_key(
                Organization.objects.filter(user=self.organization.user)
            )
        super().save(*args, **kwargs)
