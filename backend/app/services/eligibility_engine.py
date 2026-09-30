from typing import Any, Dict, List, Optional


def normalize_value(value: Any) -> Any:
    """
    Clean a value received from the frontend.
    """

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        return value

    return value


def to_number(value: Any):
    """
    Convert a value to a number.
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):

        cleaned = (
            value
            .replace(",", "")
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        try:
            return float(cleaned)

        except ValueError:
            return None

    return None


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _compare_condition_value(actual: Any, expected: Any, operator: str) -> bool:
    operator = (operator or "equals").lower()

    if operator in {"equals", "=", "=="}:
        return _normalise_text(actual) == _normalise_text(expected)

    if operator in {"not_equals", "!=", "<>"}:
        return _normalise_text(actual) != _normalise_text(expected)

    if operator == "in":
        expected_items = expected if isinstance(expected, list) else [expected]
        actual_text = _normalise_text(actual)
        return any(actual_text == _normalise_text(item) for item in expected_items)

    if operator == "contains":
        return _normalise_text(expected) in _normalise_text(actual)

    if operator in {"greater_than", ">"}:
        actual_number = to_number(actual)
        expected_number = to_number(expected)
        if actual_number is None or expected_number is None:
            return False
        return actual_number > expected_number

    if operator in {"less_than", "<"}:
        actual_number = to_number(actual)
        expected_number = to_number(expected)
        if actual_number is None or expected_number is None:
            return False
        return actual_number < expected_number

    if operator in {"greater_than_or_equal", ">="}:
        actual_number = to_number(actual)
        expected_number = to_number(expected)
        if actual_number is None or expected_number is None:
            return False
        return actual_number >= expected_number

    if operator in {"less_than_or_equal", "<="}:
        actual_number = to_number(actual)
        expected_number = to_number(expected)
        if actual_number is None or expected_number is None:
            return False
        return actual_number <= expected_number

    return False


def _evaluate_condition(condition: Optional[Dict[str, Any]], user_data: Dict[str, Any]) -> bool:
    if condition is None:
        return True

    if not isinstance(condition, dict):
        return True

    if "all" in condition:
        return all(
            _evaluate_condition(item, user_data)
            for item in (condition.get("all") or [])
        )

    if "any" in condition:
        return any(
            _evaluate_condition(item, user_data)
            for item in (condition.get("any") or [])
        )

    if "not" in condition or "not_" in condition:
        negated = condition.get("not")
        if negated is None:
            negated = condition.get("not_")
        return not _evaluate_condition(negated, user_data)

    field = condition.get("field")
    if field is None:
        return True

    actual_value = normalize_value(user_data.get(field))
    if actual_value is None:
        return False

    operator = condition.get("operator", "equals")
    expected_value = condition.get("value")
    return _compare_condition_value(actual_value, expected_value, operator)


def criterion_applies(criterion: Dict[str, Any], user_data: Dict[str, Any]) -> bool:
    """
    Return True when a criterion applies to the provided applicant profile.
    Universal rules return True when applies_when is absent or null.
    """
    if criterion is None:
        return True

    applies_when = criterion.get("applies_when")
    if applies_when is None:
        return True

    return _evaluate_condition(applies_when, user_data)


def compare_values(
    user_value: Any,
    criterion: Dict[str, Any],
) -> bool:

    operator = criterion.get("operator")

    required_value = criterion.get("value")

    minimum = criterion.get("minimum")

    maximum = criterion.get("maximum")

    options = criterion.get("options") or []

    if operator == "between":
        number = to_number(user_value)
        if number is None:
            return False
        if minimum is not None and number < minimum:
            return False
        if maximum is not None and number > maximum:
            return False
        return True

    if operator == ">=":
        user_number = to_number(user_value)
        required_number = to_number(required_value) if required_value is not None else minimum
        if user_number is None or required_number is None:
            return False
        return user_number >= required_number

    if operator == "<=":
        user_number = to_number(user_value)
        required_number = to_number(required_value) if required_value is not None else maximum
        if user_number is None or required_number is None:
            return False
        return user_number <= required_number

    if operator == ">":
        user_number = to_number(user_value)
        required_number = to_number(required_value)
        if user_number is None or required_number is None:
            return False
        return user_number > required_number

    if operator == "<":
        user_number = to_number(user_value)
        required_number = to_number(required_value)
        if user_number is None or required_number is None:
            return False
        return user_number < required_number

    if operator == "=":
        return _normalise_text(user_value) == _normalise_text(required_value)

    if operator == "!=":
        return _normalise_text(user_value) != _normalise_text(required_value)

    if operator == "in":
        user_string = _normalise_text(user_value)
        return any(user_string == _normalise_text(option) for option in options)

    if operator == "contains":
        if user_value is None:
            return False
        user_string = _normalise_text(user_value)
        required_string = _normalise_text(required_value)
        return required_string in user_string

    return False


def build_reason(
    criterion: Dict[str, Any],
    user_value: Any,
    passed: bool,
) -> str:

    name = criterion.get("name", "This criterion")
    description = criterion.get("description", "")

    if passed:
        return f"{name} requirement is satisfied."

    operator = criterion.get("operator")
    minimum = criterion.get("minimum")
    maximum = criterion.get("maximum")
    required_value = criterion.get("value")
    unit = criterion.get("unit")

    if operator == ">=":
        required = minimum if minimum is not None else required_value
        return (
            f"{name} requires at least {required}"
            f"{' ' + unit if unit else ''}. Your value is {user_value}."
        )

    if operator == "<=":
        required = maximum if maximum is not None else required_value
        return (
            f"{name} must be at most {required}"
            f"{' ' + unit if unit else ''}. Your value is {user_value}."
        )

    if operator == "between":
        return (
            f"{name} must be between {minimum} and {maximum}"
            f"{' ' + unit if unit else ''}. Your value is {user_value}."
        )

    if operator == "in":
        options = criterion.get("options", [])
        return (
            f"{name} must be one of: {', '.join(map(str, options))}. "
            f"Your value is {user_value}."
        )

    if operator == "=":
        return f"{name} must be {required_value}. Your value is {user_value}."

    if description:
        return f"{name} does not satisfy the requirement: {description}"

    return f"{name} does not satisfy the eligibility requirement."


def evaluate_eligibility(
    criteria: List[Dict[str, Any]],
    user_data: Dict[str, Any],
) -> Dict[str, Any]:

    results = []
    passed_criteria = []
    failed_criteria = []
    missing_criteria = []
    not_applicable_criteria = []

    for criterion in criteria:
        criterion_id = criterion.get("id")
        name = criterion.get("name", criterion_id)

        if not criterion_applies(criterion, user_data):
            results.append({
                "criterion": criterion,
                "status": "not_applicable",
                "passed": None,
                "user_value": normalize_value(user_data.get(criterion_id)),
                "reason": f"{name} does not apply to the selected applicant profile.",
            })
            not_applicable_criteria.append(criterion)
            continue

        user_value = normalize_value(user_data.get(criterion_id))

        if user_value is None:
            result = {
                "criterion": criterion,
                "status": "missing",
                "passed": False,
                "user_value": None,
                "reason": f"{name} information was not provided.",
            }
            results.append(result)
            missing_criteria.append(result)
            continue

        passed = compare_values(user_value, criterion)
        reason = build_reason(criterion, user_value, passed)

        if passed:
            status = "passed"
            passed_criteria.append(criterion)
        else:
            status = "failed"
            failed_criteria.append(criterion)

        results.append({
            "criterion": criterion,
            "status": status,
            "passed": passed,
            "user_value": user_value,
            "reason": reason,
        })

    mandatory_failures = [
        item for item in failed_criteria if item.get("mandatory", True)
    ]
    mandatory_missing = [
        item for item in missing_criteria if item.get("mandatory", True)
    ]

    if mandatory_failures:
        eligible = False
        message = "You do not satisfy one or more mandatory eligibility criteria."
    elif mandatory_missing:
        eligible = None
        message = "Eligibility cannot be determined until all mandatory information is provided."
    else:
        eligible = True
        message = "You satisfy all evaluated mandatory eligibility criteria."

    return {
        "eligible": eligible,
        "message": message,
        "total_criteria": len(criteria),
        "applicable_count": len(criteria) - len(not_applicable_criteria),
        "passed_count": len(passed_criteria),
        "failed_count": len(failed_criteria),
        "missing_count": len(missing_criteria),
        "not_applicable_count": len(not_applicable_criteria),
        "results": results,
    }