"""
String Utilities - Helper functions for string operations
"""
import re


def generate_prefix(clinic_name):
    """
    Generates a short, unique prefix from a clinic name.

    Args:
        clinic_name (str): Full name of the clinic

    Returns:
        str: Short prefix (max 4 chars) derived from clinic name

    Example:
        >>> generate_prefix("Clínica RedSalud Santiago")
        'sant'
    """
    name_parts = clinic_name.replace("Clínica RedSalud", "").strip().lower()
    prefix = re.sub(r'[^a-z]', '', name_parts)[:4]
    return prefix
