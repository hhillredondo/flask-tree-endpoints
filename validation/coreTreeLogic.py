from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


fmt = "%Y-%m-%dT%H:%M:%SZ"
DISTANT_FUTURE_DATE = datetime(9999, 1, 1)


def validate_life_date_order(born, died):
    try:
        born_date = datetime.strptime(born, fmt)
        died_date = datetime.strptime(died, fmt)
        if born_date > died_date:
            return False, "Date of birth must be earlier than date of death"
        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def validate_max_lifespan(born, died, max_years: int = 120):
    try:
        born_date = datetime.strptime(born, fmt)
        died_date = datetime.strptime(died, fmt)
        if died_date > born_date + relativedelta(years=max_years):
            return False, "Humans cannot live that long"
        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def validate_parents_number(number_of_parents):
    if number_of_parents == 1:
        return (
            False,
            "Member already has 1 parent. Create a spouse to the parent instead.",
        )
    if number_of_parents == 2:
        return False, "Member already has 2 parents"
    elif number_of_parents < 2:
        return True, ""


def validate_parent_is_alive_and_fertile(
    parent_gender, parent_born, parent_died, child_born
):
    maximum_ages = {
        "male": 100,
        "female": 60,
    }
    parent_names = {
        "male": "Father",
        "female": "Mother",
    }
    parent_name = parent_names.get(parent_gender)
    try:
        parent_born_date = datetime.strptime(parent_born, fmt)
        child_born_date = datetime.strptime(child_born, fmt)
        if parent_died is None or parent_died == "":
            parent_died_date = None
        else:
            parent_died_date = datetime.strptime(parent_died, fmt)

        if parent_died_date is not None:
            if not parent_born_date < child_born_date < parent_died_date:
                return (False, f"Child must be born within {parent_name}'s lifetime")
        else:
            if parent_born_date >= child_born_date:
                return (False, f"Child must be born after {parent_name}'s birth")

        minimum_age = timedelta(days=(12 * 365 + 9 * 30))
        maximum_age = timedelta(days=(maximum_ages.get(parent_gender) * 365))
        age_difference = child_born_date - parent_born_date

        if age_difference < minimum_age:
            return (
                False,
                f"{parent_name} must be at least 12 years old to have a child.",
            )
        if age_difference > maximum_age:
            return False, f"{parent_name} must be under 60 years old to have a child."

        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def validate_heterosexual_marriage(first_gender, second_gender):
    if first_gender == second_gender:
        return False, "Spouses cannot have the same gender"
    return True, ""


def validate_siblings_birth_dates(born, siblings_born):
    try:
        born_date = datetime.strptime(born, fmt)
        children_born_together = []
        nine_months = timedelta(days=9 * 30)

        for sibling_born in siblings_born:
            sibling_born_date = datetime.strptime(sibling_born, fmt)

            if sibling_born_date == born_date:
                children_born_together.append(sibling_born)
            else:
                if abs((born_date - sibling_born_date).days) < nine_months.days:
                    return (
                        False,
                        f"Child cannot be born less than 9 months before or after a sibling's birth date: {sibling_born}",
                    )

        if len(children_born_together) > 8:
            return (
                False,
                "A child may share an exact birth date with up to 8 siblings only.",
            )

        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def validate_groom_and_bride_single_status(
    marriage_date, groom_marriages, bride_marriages
):
    if len(groom_marriages) == 0 & len(bride_marriages) == 0:
        return True, ""

    try:
        marriage_date_parsed = datetime.strptime(marriage_date, fmt)

        def is_single_at_marriage(marriages, marriage_date):
            if len(marriages) == 0:
                return True, ""
            for marriage in marriages:
                start_date = datetime.strptime(marriage["married"], fmt)
                end_date = (
                    datetime.strptime(marriage["divorced"], fmt)
                    if marriage["divorced"]
                    else None
                )

                if end_date:
                    if start_date <= marriage_date <= end_date:
                        return (
                            False,
                            f"Person is still married from {start_date.strftime(fmt)} to {end_date.strftime(fmt)}.",
                        )
                else:
                    if start_date <= marriage_date:
                        return (
                            False,
                            f"Person is still married since {start_date.strftime(fmt)}.",
                        )

            return True, ""

        groom_status, groom_message = is_single_at_marriage(
            groom_marriages, marriage_date_parsed
        )
        if not groom_status:
            return False, f"Groom: {groom_message}"

        bride_status, bride_message = is_single_at_marriage(
            bride_marriages, marriage_date_parsed
        )
        if not bride_status:
            return False, f"Bride: {bride_message}"

        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def verify_legal_marriage_age(born, married):
    try:
        born_date = datetime.strptime(born, fmt)
        married_date = datetime.strptime(married, fmt)

        if married_date < born_date:
            return False, "Marriage date cannot be before birth date"

        diff = abs(married_date.year - born_date.year)

        if (married_date.month, married_date.day) < (born_date.month, born_date.day):
            diff -= 1

        if diff >= 16:
            return True, ""

        return False, "Member must be at least 16 to get married"
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def verify_marriage_divorce_date_order(married, divorced):

    try:
        married_date = datetime.strptime(married, fmt)
        if divorced is None:
            return True, ""
        divorced_date = datetime.strptime(divorced, fmt)
        if married_date > divorced_date:
            return False, "Divorce must come after marriage"
        return True, ""
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def verify_common_children_born_in_marriage(children_born, married, divorced):
    married_date = datetime.strptime(married, fmt)
    if divorced is None:
        divorced_date = DISTANT_FUTURE_DATE
    else:
        divorced_date = datetime.strptime(divorced, fmt)

    for child_born in children_born:
        child_born_date = datetime.strptime(child_born, fmt)
        if not married_date < child_born_date < divorced_date + relativedelta(months=9):
            return (
                False,
                "Child's date of birth has to be within parents' marriage (or up to 9 months after)",
            )

    return True, ""


def verify_member_is_deletable(relations):
    if relations >= 2:
        return False, "Member with 2 or more relations cannot be deleted"
    elif relations < 2:
        return True, ""
