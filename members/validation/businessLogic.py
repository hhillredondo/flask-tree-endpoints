from datetime import datetime

# TO-DO: Check date format is correct!
def validate_date_order(born, died, fmt="%Y-%m-%d"):
    if datetime.strptime(born, fmt) > datetime.strptime(died, fmt):
        return False, "Date of birth must be earlier than date of death"
    return True, ""