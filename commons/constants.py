# constants.py
from django.conf import settings

from commons.tax_code_constants import ITEM_TAX_CODE_CHOICES

# API Endpoints
API_ENDPOINTS = {
    "saveItem": "/saveItem",
    "saveCustomer": "/saveBhfCustomer",
    "saveTransaction": "/saveTransaction",
    "fetchItemClassification": "/selectItemClsList",
    "fetchTaxCode": "/selectCodeList",
    "saveStockMovement": "/insertStockIO",
    "saveSalesTransaction": "/saveTrnsSalesOsdc",
    "saveCreditNote": "/saveTrnsSalesOsdc",
    "selectTrnsPurchaseSalesList": "/selectTrnsPurchaseSalesList",
    "updatePurchases": "/selectTrnsPurchaseSalesList",
    "verifyPurchase": "/selectImportItemList",
    "updateImports": "/selectImportList",
    "saveItemComposition": "/saveItemComposition",
    "fetchImports": "/selectImportItemList",
    "initializeDevice": "/initializer/selectInitInfo",
    "fetchBranches": "/selectBhfList",
    "fetchNotices": "/selectNoticeList"
}

# SAR Type Codes
SAR_TYPE_CODES = {
    "ADD": {
        "Import": "01",
        "Purchase": "02",
        "Return": "03",
        "Stock Movement": "04",
        "Processing": "05",
        "Adjustment": "06",
    },
    "REMOVE": {
        "Sale": "11",
        "Return": "12",
        "Stock Movement": "13",
        "Processing": "14",
        "Discarding": "15",
        "Adjustment": "16",
    }
}

# Movement Type Codes
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
# TAX_TYPE_CHOICES = [
#     ("A", "A-Exempt"),
#     ("B", "B-16.00%"),
#     ("C", "C-0%"),
#     ("D", "D-Non-VAT"),
#     ("E", "E-8%"),
# ]


def get_tax_type_choices():
    for item in ITEM_TAX_CODE_CHOICES:
        if item["cdClsNm"] == "Taxation Type":  # Find the correct class
            return [(tax["cd"], tax["cdNm"]) for tax in item["dtlList"]]

    return [
        ("A", "A-Exempt"),
        ("B", "B-16.00%"),
        ("C", "C-0%"),
        ("D", "D-Non-VAT"),
        ("E", "E-8%"),
    ]  # Return  if not found


TAX_TYPE_CHOICES = get_tax_type_choices()


TAX_RATES = {
    "A": 0,    # Exempt
    "B": 16,   # 16% VAT
    "C": 0,    # 0% VAT
    "D": 0,    # Non-VAT
    "E": 8,    # 8% VAT
}

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
