from django.db.models import QuerySet
from django.db import transaction


def generate_organization_pin(user):
    """
    Generate a sequential organization pin starting from '0000001'
    unique per user.
    """
    from organization.models import Organization

    # Get the last PIN for the user, ordered by descending organization_pin
    last_pin = (
        Organization.objects.filter(user=user)
        .order_by("-organization_pin")
        .values_list("organization_pin", flat=True)
        .first()
    )
    next_number = int(last_pin) + 1 if last_pin else 1
    return f"{next_number:07d}"


def generate_customer_pin(organization):
    """
    Generate a sequential customer pin starting from '0000001'
    unique per organization.
    """
    from customer.models import Customer

    # Get the last customer pin for the given organization, ordered by descending customer_pin
    last_pin = (
        Customer.objects.filter(organization=organization)
        .order_by("-customer_pin")
        .values_list("customer_pin", flat=True)
        .first()
    )
    next_number = int(last_pin) + 1 if last_pin else 1
    return f"{next_number:07d}"


def generate_item_cd(self):
    """
    Generate a unique item code that includes sequential number specific to
    the country, product type, packaging, and quantity unit.
    """

    from item.models import Item
    country_code = self.origin_nation_code  # e.g., KE for Kenya
    product_type = self.item_type_code  # e.g., 2 for Finished Product
    package_unit = self.package_unit_code  # e.g., NT for NET
    quantity_unit = self.quantity_unit_code  # e.g., BA for Barrel

    # Build the prefix based on the provided fields
    prefix = f"{country_code}{product_type}{package_unit}{quantity_unit}"

    with transaction.atomic():
        # Get the last item's numeric part (last 7 digits) within the organization
        last_item = (
            Item.objects.filter(organization=self.organization)
            # Ignore invalid numeric suffix
            .exclude(itemCd__regex=r"\D{0,}[^0-9]{7}$")
            .order_by('-itemCd')  # Order by `itemCd`
            .first()
        )
        # print(last_item)

        # Extract and increment the numeric part
        if last_item and last_item.itemCd[-7:].isdigit():
            last_number = int(last_item.itemCd[-7:])
        else:
            last_number = 0

        next_number = last_number + 1
        increment = f"{next_number:07d}"  # Ensure zero-padded to 7 digits
        print(increment)
        # Generate the new item code
        return f"{prefix}{increment}"


def get_choices_as_autocomplete(choices, query):
    """Filter and format choices for autocomplete."""
    query = query.lower()
    return [
        {"id": code, "text": name}
        for code, name in choices
        if query in name.lower() or query in code.lower()
    ]
    
