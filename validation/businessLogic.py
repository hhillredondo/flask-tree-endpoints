from datetime import datetime


def validate_date_order(born, died, fmt="%Y-%m-%dT%H:%M:%SZ"):
    try:
        born_date = datetime.strptime(born, fmt)
        died_date = datetime.strptime(died, fmt)
        if born_date > died_date:
            return False, "Date of birth must be earlier than date of death"
        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"
