"""Comprehensive tests for applicability-aware extraction and evaluation."""

import pytest
from app.services.extractor import extract_eligibility_with_ai
from app.services.eligibility_engine import criterion_applies, evaluate_eligibility


class TestExtractionPreservesAllRules:
    """Test A: Extraction preserves multiple conditional rules."""

    def test_multiple_education_levels_extracted_as_separate_criteria(self):
        """UG + PG + PhD rules should be extracted as separate criteria."""
        page = {
            'url': 'https://test.com',
            'title': 'Multi-level Scholarship',
            'full_text': '''
            Scholarship Programme
            
            UNDERGRADUATE: Must be pursuing undergraduate. Minimum 60% marks. 
            Income below INR 2,50,000.
            
            POSTGRADUATE: Pursuing postgraduate courses. Minimum 53% marks. 
            Income below INR 3,00,000.
            
            PhD: Enrolled in PhD program. Research proposal required. 
            Income below INR 4,00,000. Minimum 55% marks.
            '''
        }
        
        result = extract_eligibility_with_ai(page)
        
        # Should extract criteria for UG, PG, and PhD
        assert len(result.criteria) >= 9, f"Expected at least 9 criteria, got {len(result.criteria)}"
        
        # Should have criteria from each education level
        criterion_names = [c.name for c in result.criteria]
        has_ug = any('undergraduate' in name.lower() for name in criterion_names)
        has_pg = any('postgraduate' in name.lower() for name in criterion_names)
        has_phd = any('phd' in name.lower() or 'research' in name.lower() for name in criterion_names)
        
        assert has_ug, "Should extract undergraduate criteria"
        assert has_pg, "Should extract postgraduate criteria"
        assert has_phd, "Should extract PhD criteria"


class TestAnalysisPageDisplaysAllRules:
    """Test B: Analysis page receives and displays all rules."""

    def test_analysis_returns_all_criteria_regardless_of_user(self):
        """All extracted criteria should be returned, not filtered by applicability."""
        page = {
            'url': 'https://test.com',
            'title': 'Test',
            'full_text': '''
            Scholarship
            UNDERGRADUATE: 60% required. Income limit 2.5L.
            POSTGRADUATE: 53% required. Income limit 3L.
            PhD: Research proposal required. Income limit 4L. 55% required.
            '''
        }
        
        result = extract_eligibility_with_ai(page)
        criteria_count = len(result.criteria)
        
        # All criteria should be present regardless of education_level
        # (The frontend will display all of them)
        assert criteria_count >= 7, f"Expected at least 7 criteria, got {criteria_count}"


class TestUGUserQuestionnaire:
    """Test C: UG user questionnaire only shows UG-relevant questions."""

    def test_ug_user_marked_criteria_as_applicable(self):
        """UG-specific criteria should be applicable for UG users."""
        criteria = [
            {
                "id": "ug_marks",
                "name": "UG Academic Performance",
                "category": "academic_performance",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "undergraduate"
                },
                "source_text": "Test",
            },
            {
                "id": "pg_marks",
                "name": "PG Academic Performance",
                "category": "academic_performance",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "postgraduate"
                },
                "source_text": "Test",
            },
        ]
        
        ug_data = {"education_level": "undergraduate"}
        
        # UG criterion should apply
        assert criterion_applies(criteria[0], ug_data) is True
        # PG criterion should NOT apply
        assert criterion_applies(criteria[1], ug_data) is False


class TestPGUserQuestionnaire:
    """Test D: PG user questionnaire only shows PG-relevant questions."""

    def test_pg_user_marked_criteria_as_applicable(self):
        """PG-specific criteria should be applicable for PG users."""
        criteria = [
            {
                "id": "ug_marks",
                "name": "UG Academic Performance",
                "category": "academic_performance",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "undergraduate"
                },
                "source_text": "Test",
            },
            {
                "id": "pg_marks",
                "name": "PG Academic Performance",
                "category": "academic_performance",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "postgraduate"
                },
                "source_text": "Test",
            },
        ]
        
        pg_data = {"education_level": "postgraduate"}
        
        # UG criterion should NOT apply
        assert criterion_applies(criteria[0], pg_data) is False
        # PG criterion should apply
        assert criterion_applies(criteria[1], pg_data) is True


class TestUGUserEligibility:
    """Test E: UG user - PG rule is NOT_APPLICABLE."""

    def test_ug_user_pg_rule_not_applicable(self):
        """For UG user, PG rule should be marked as NOT_APPLICABLE."""
        criteria = [
            {
                "id": "ug_marks",
                "name": "UG Marks",
                "category": "academic_performance",
                "data_type": "percentage",
                "operator": ">=",
                "value": "60",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "undergraduate"
                },
                "source_text": "Test",
            },
            {
                "id": "pg_marks",
                "name": "PG Marks",
                "category": "academic_performance",
                "data_type": "percentage",
                "operator": ">=",
                "value": "53",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "postgraduate"
                },
                "source_text": "Test",
            },
        ]
        
        result = evaluate_eligibility(criteria, {
            "education_level": "undergraduate",
            "ug_marks": "65"
        })
        
        # UG criterion should pass
        ug_result = next(r for r in result['results'] if r['criterion']['id'] == 'ug_marks')
        assert ug_result['status'] == 'passed'
        
        # PG criterion should be NOT_APPLICABLE
        pg_result = next(r for r in result['results'] if r['criterion']['id'] == 'pg_marks')
        assert pg_result['status'] == 'not_applicable'


class TestPGUserEligibility:
    """Test F: PG user - UG rule is NOT_APPLICABLE."""

    def test_pg_user_ug_rule_not_applicable(self):
        """For PG user, UG rule should be marked as NOT_APPLICABLE."""
        criteria = [
            {
                "id": "ug_marks",
                "name": "UG Marks",
                "category": "academic_performance",
                "data_type": "percentage",
                "operator": ">=",
                "value": "60",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "undergraduate"
                },
                "source_text": "Test",
            },
            {
                "id": "pg_marks",
                "name": "PG Marks",
                "category": "academic_performance",
                "data_type": "percentage",
                "operator": ">=",
                "value": "53",
                "mandatory": True,
                "conditional": True,
                "applies_when": {
                    "field": "education_level",
                    "operator": "equals",
                    "value": "postgraduate"
                },
                "source_text": "Test",
            },
        ]
        
        result = evaluate_eligibility(criteria, {
            "education_level": "postgraduate",
            "pg_marks": "55"
        })
        
        # UG criterion should be NOT_APPLICABLE
        ug_result = next(r for r in result['results'] if r['criterion']['id'] == 'ug_marks')
        assert ug_result['status'] == 'not_applicable'
        
        # PG criterion should pass
        pg_result = next(r for r in result['results'] if r['criterion']['id'] == 'pg_marks')
        assert pg_result['status'] == 'passed'


class TestUniversalIncomeRule:
    """Test G: Universal income rule applies to both UG and PG."""

    def test_universal_income_applies_to_all(self):
        """Income rule with no applicability should apply to everyone."""
        criteria = [
            {
                "id": "income",
                "name": "Family Income",
                "category": "income",
                "data_type": "currency",
                "operator": "<=",
                "value": "250000",
                "mandatory": True,
                "conditional": False,
                "applies_when": None,  # UNIVERSAL
                "source_text": "Universal income limit",
            },
        ]
        
        # Should apply to UG user
        ug_data = {"education_level": "undergraduate", "income": "200000"}
        assert criterion_applies(criteria[0], ug_data) is True
        
        # Should apply to PG user
        pg_data = {"education_level": "postgraduate", "income": "200000"}
        assert criterion_applies(criteria[0], pg_data) is True


class TestDocumentRequirements:
    """Test H: Documents visible in policy analysis, applicable only requested from applicant."""

    def test_all_documents_extracted_with_applicability(self):
        """All documents should be extracted including applicability conditions."""
        page = {
            'url': 'https://test.com',
            'title': 'Test',
            'full_text': '''
            Scholarship
            Universal: Income certificate required.
            UG: Submit admission receipt.
            PhD: Research proposal and registration document required.
            '''
        }
        
        result = extract_eligibility_with_ai(page)
        
        # Should extract multiple documents
        assert len(result.required_documents) >= 4, \
            f"Expected at least 4 documents, got {len(result.required_documents)}"
        
        # Documents should have applicability conditions
        has_universal = any(doc.applies_when is None for doc in result.required_documents)
        has_conditional = any(doc.applies_when is not None for doc in result.required_documents)
        
        assert has_universal, "Should have at least one universal document"
        assert has_conditional, "Should have at least one conditional document"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
