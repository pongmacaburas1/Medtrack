
from django import template

register = template.Library()

@register.filter
def count_low_stock(medications):
    """Count medications with low stock"""
    count = 0
    for med in medications:
        inventory = med.medicationinventory_set.first()
        if inventory and inventory.is_low_stock:
            count += 1
    return count

@register.filter
def count_expired(medications):
    """Count expired medications"""
    count = 0
    for med in medications:
        inventory = med.medicationinventory_set.first()
        if inventory and inventory.is_expired:
            count += 1
    return count

@register.filter
def count_in_stock(medications):
    """Count medications in stock (not low, not expired)"""
    count = 0
    for med in medications:
        inventory = med.medicationinventory_set.first()
        if inventory and not inventory.is_low_stock and not inventory.is_expired:
            count += 1
    return count