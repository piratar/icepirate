
# Incomplete implementation. Required a varity checks.
def is_icelandic_ssn(ssn):
    # Must be 10 characters long.
    if len(ssn) != 10:
        return False

    # Must be digit.
    if not ssn.isdigit():
        return False

    return True

