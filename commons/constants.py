# constants.py
API_BASE_URL = "https://etims-api-sbx.kra.go.ke/etims-api"

API_ENDPOINTS = {
    "saveItem": f"{API_BASE_URL}/saveItem",
    "saveCustomer": f"{API_BASE_URL}/saveCustomer",
    "saveTransaction": f"{API_BASE_URL}/saveTransaction",
}

MOVEMENT_TYPE_CHOICES = [
    ('ADD', 'Addition'),
    ('REMOVE', 'Removal'),
    ('TRANSFER', 'Transfer'),
]

# Country Choices
COUNTRY_CHOICES = [
    ('KE', 'KENYA'),
    ('US', 'UNITED STATES'),
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

# Tax Type Choices
TAX_TYPE_CHOICES = [
    ("A", "A-Exempt"),
    ("B", "B-16.00%"),
    ("C", "C-0%"),
    ("D", "D-Non-VAT"),
    ("E", "E-8%"),
]

# Taxpayer Status Choices
TAXPAYER_STATUS_CHOICES = [
    ("A", "Active"),
    ("D", "Inactive"),
]

# Product Type Choices
PRODUCT_TYPE_CHOICES = [
    ("1", "Raw Material"),
    ("2", "Finished Product"),
    ("3", "Service without stock"),
]

# Unit Choices
UNIT_CHOICES = [
    ('4B', 'Pair'),
    ('BA', 'Barrel'),
    ('BE', 'Bundle'),
    ('BG', 'Bag'),
    ('BL', 'Block'),
    ('BLL', 'BLL Barrel (petroleum)'),
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
    ('U', 'Pieces/item [Number]'),
    ('YRD', 'Yard'),
]

# Package Choices
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
