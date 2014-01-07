
def is_kennitala(kennitala):
    # Must be 10 characters long.
    if len(kennitala) != 10:
        return False

    # Must be digit.
    if not kennitala.isdigit():
        return False

    return True

