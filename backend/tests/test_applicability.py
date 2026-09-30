from app.services.eligibility_engine import criterion_applies, evaluate_eligibility


def test_universal_income_rule_applies_to_everyone():
    criterion = {
        "id": "annual_income",
        "name": "Annual family income",
        "category": "income",
        "data_type": "currency",
        "operator": "<=",
        "maximum": 250000,
        "mandatory": True,
        "conditional": False,
        "source_text": "Annual family income should not exceed Rs. 2.5 lakh.",
        "applies_when": None,
    }

    assert criterion_applies(criterion, {}) is True
    assert criterion_applies(criterion, {"education_level": "undergraduate"}) is True


def test_ug_rule_applies_for_undergraduate():
    criterion = {
        "id": "ug_percentage",
        "name": "Undergraduate percentage",
        "category": "academic_performance",
        "data_type": "percentage",
        "operator": ">=",
        "minimum": 60,
        "mandatory": True,
        "conditional": True,
        "condition_description": "Students pursuing undergraduate courses.",
        "source_text": "Undergraduate applicants must have at least 60%.",
        "applies_when": {"field": "education_level", "operator": "equals", "value": "undergraduate"},
    }

    assert criterion_applies(criterion, {"education_level": "undergraduate"}) is True


def test_pg_rule_does_not_apply_for_undergraduate():
    criterion = {
        "id": "pg_percentage",
        "name": "Postgraduate percentage",
        "category": "academic_performance",
        "data_type": "percentage",
        "operator": ">=",
        "minimum": 53,
        "mandatory": True,
        "conditional": True,
        "condition_description": "Postgraduate students must have at least 53%.",
        "source_text": "Postgraduate applicants must have at least 53%.",
        "applies_when": {"field": "education_level", "operator": "equals", "value": "postgraduate"},
    }

    assert criterion_applies(criterion, {"education_level": "undergraduate"}) is False


def test_pg_rule_applies_for_postgraduate():
    criterion = {
        "id": "pg_percentage",
        "name": "Postgraduate percentage",
        "category": "academic_performance",
        "data_type": "percentage",
        "operator": ">=",
        "minimum": 53,
        "mandatory": True,
        "conditional": True,
        "condition_description": "Postgraduate students must have at least 53%.",
        "source_text": "Postgraduate applicants must have at least 53%.",
        "applies_when": {"field": "education_level", "operator": "equals", "value": "postgraduate"},
    }

    assert criterion_applies(criterion, {"education_level": "postgraduate"}) is True


def test_ug_applicant_fails_ug_rule_but_ignores_pg_rule():
    criteria = [
        {
            "id": "ug_percentage",
            "name": "Undergraduate percentage",
            "category": "academic_performance",
            "data_type": "percentage",
            "operator": ">=",
            "minimum": 60,
            "mandatory": True,
            "conditional": True,
            "source_text": "Undergraduate applicants must have at least 60%.",
            "applies_when": {"field": "education_level", "operator": "equals", "value": "undergraduate"},
        },
        {
            "id": "pg_percentage",
            "name": "Postgraduate percentage",
            "category": "academic_performance",
            "data_type": "percentage",
            "operator": ">=",
            "minimum": 53,
            "mandatory": True,
            "conditional": True,
            "source_text": "Postgraduate applicants must have at least 53%.",
            "applies_when": {"field": "education_level", "operator": "equals", "value": "postgraduate"},
        },
    ]

    result = evaluate_eligibility(criteria, {"education_level": "undergraduate", "ug_percentage": 50})

    assert result["eligible"] is False
    assert any(item["criterion"]["id"] == "ug_percentage" and item["status"] == "failed" for item in result["results"])
    assert all(item["criterion"]["id"] != "pg_percentage" or item["status"] == "not_applicable" for item in result["results"])


def test_multiple_conditions_must_match():
    criterion = {
        "id": "renewal_pg_rule",
        "name": "Postgraduate renewal rule",
        "category": "academic_performance",
        "data_type": "percentage",
        "operator": ">=",
        "minimum": 65,
        "mandatory": True,
        "conditional": True,
        "condition_description": "Renewal applicants enrolled in postgraduate courses.",
        "source_text": "Renewal postgraduate applicants must have at least 65%.",
        "applies_when": {
            "all": [
                {"field": "application_type", "operator": "equals", "value": "renewal"},
                {"field": "education_level", "operator": "equals", "value": "postgraduate"},
            ]
        },
    }

    assert criterion_applies(criterion, {"application_type": "renewal", "education_level": "postgraduate"}) is True
    assert criterion_applies(criterion, {"application_type": "fresh", "education_level": "postgraduate"}) is False
    assert criterion_applies(criterion, {"application_type": "renewal", "education_level": "undergraduate"}) is False
