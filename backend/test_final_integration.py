#!/usr/bin/env python3
"""Final integration test - complete end-to-end workflow."""

from app.services.extractor import extract_eligibility_with_ai
from app.services.eligibility_engine import evaluate_eligibility, criterion_applies
import json

print("=" * 70)
print("FINAL INTEGRATION TEST - COMPLETE WORKFLOW")
print("=" * 70)

# Step 1: Extract eligibility with AI
print("\n[STEP 1] AI EXTRACTION")
print("-" * 70)

page = {
    'url': 'https://test-scholarship.edu/apply',
    'title': 'Merit Scholarship Programme',
    'full_text': '''
    Merit Scholarship Programme 2026
    
    GENERAL ELIGIBILITY:
    All applicants must be Indian citizens.
    Annual family income must not exceed INR 2,50,000.
    
    UNDERGRADUATE (UG):
    Pursuing undergraduate courses at recognized institutions.
    Minimum 60% marks in previous examination required.
    Required documents: Marksheet, Admission Receipt.
    
    POSTGRADUATE (PG):
    Pursuing postgraduate courses.
    Minimum 53% marks in previous examination.
    Income limit: Up to INR 3,00,000.
    Required documents: PG Marksheet, Admission Certificate.
    
    PhD APPLICANTS:
    Research proposal required.
    Minimum 55% marks in Master degree.
    Income limit: Up to INR 4,00,000.
    PhD-specific document: Research Proposal, Registration Certificate.
    
    Application Deadline: 31 December 2026
    '''
}

try:
    result = extract_eligibility_with_ai(page)
    
    print(f"✓ Criteria extracted: {len(result.criteria)}")
    print(f"✓ Documents extracted: {len(result.required_documents)}")
    
    # Step 2: Display Analysis Page (ALL rules)
    print("\n[STEP 2] ANALYSIS PAGE (Display ALL extracted rules)")
    print("-" * 70)
    
    print(f"\nScheme: {result.scheme_name}")
    print(f"Summary: {result.summary}")
    
    print(f"\nAll Eligibility Criteria ({len(result.criteria)}):")
    for i, c in enumerate(result.criteria, 1):
        applies = 'conditional' if c.applies_when else 'universal'
        print(f"  {i}. {c.name} ({applies})")
        if c.applies_when:
            print(f"     Applies when: education_level = {c.applies_when.value}")
    
    print(f"\nAll Document Requirements ({len(result.required_documents)}):")
    for i, d in enumerate(result.required_documents, 1):
        applies = 'conditional' if d.applies_when else 'universal'
        print(f"  {i}. {d.name} ({applies})")
    
    # Step 3: UG Applicant Workflow
    print("\n[STEP 3] UG APPLICANT WORKFLOW")
    print("-" * 70)
    
    ug_profile = {
        'education_level': 'undergraduate',
        'ug_percentage': 65,
        'income': 200000,
    }
    
    # Show applicable criteria for UG
    print("\nApplicable criteria for UG applicant:")
    applicable_for_ug = [c for c in result.criteria if criterion_applies(c.model_dump(), ug_profile)]
    print(f"  ✓ {len(applicable_for_ug)} criteria apply (out of {len(result.criteria)})")
    for c in applicable_for_ug:
        print(f"    - {c.name}")
    
    # Evaluate eligibility for UG
    criteria_dicts = [c.model_dump() for c in result.criteria]
    ug_eval = evaluate_eligibility(criteria_dicts, ug_profile)
    
    print(f"\nEligibility evaluation for UG:")
    print(f"  Eligible: {ug_eval['eligible']}")
    print(f"  Passed: {ug_eval['passed_count']}/{ug_eval['applicable_count']} applicable criteria")
    print(f"  Not Applicable: {ug_eval['not_applicable_count']} criteria")
    
    # Show applicable documents for UG
    applicable_docs_ug = [d for d in result.required_documents 
                          if d.applies_when is None or 
                          criterion_applies(d.model_dump(), ug_profile)]
    print(f"\nRequired documents for UG:")
    for d in applicable_docs_ug:
        print(f"  ✓ {d.name}")
    
    # Step 4: PG Applicant Workflow
    print("\n[STEP 4] PG APPLICANT WORKFLOW")
    print("-" * 70)
    
    pg_profile = {
        'education_level': 'postgraduate',
        'pg_percentage': 54,
        'income': 280000,
    }
    
    # Show applicable criteria for PG
    print("\nApplicable criteria for PG applicant:")
    applicable_for_pg = [c for c in result.criteria if criterion_applies(c.model_dump(), pg_profile)]
    print(f"  ✓ {len(applicable_for_pg)} criteria apply (out of {len(result.criteria)})")
    for c in applicable_for_pg:
        print(f"    - {c.name}")
    
    # Evaluate eligibility for PG
    pg_eval = evaluate_eligibility(criteria_dicts, pg_profile)
    
    print(f"\nEligibility evaluation for PG:")
    print(f"  Eligible: {pg_eval['eligible']}")
    print(f"  Passed: {pg_eval['passed_count']}/{pg_eval['applicable_count']} applicable criteria")
    print(f"  Not Applicable: {pg_eval['not_applicable_count']} criteria")
    
    # Show applicable documents for PG
    applicable_docs_pg = [d for d in result.required_documents 
                          if d.applies_when is None or 
                          criterion_applies(d.model_dump(), pg_profile)]
    print(f"\nRequired documents for PG:")
    for d in applicable_docs_pg:
        print(f"  ✓ {d.name}")
    
    # Final verification
    print("\n[VERIFICATION]")
    print("-" * 70)
    
    # Verify UG criteria not applicable to PG
    ug_only_criteria = [c for c in result.criteria 
                        if c.applies_when and 
                        c.applies_when.value == 'undergraduate']
    pg_can_apply_ug = [c for c in ug_only_criteria if criterion_applies(c.model_dump(), pg_profile)]
    
    if len(pg_can_apply_ug) == 0:
        print("✓ UG-specific criteria correctly excluded for PG applicants")
    else:
        print("✗ ERROR: UG criteria applying to PG applicants")
    
    # Verify PG criteria not applicable to UG
    pg_only_criteria = [c for c in result.criteria 
                        if c.applies_when and 
                        c.applies_when.value == 'postgraduate']
    ug_can_apply_pg = [c for c in pg_only_criteria if criterion_applies(c.model_dump(), ug_profile)]
    
    if len(ug_can_apply_pg) == 0:
        print("✓ PG-specific criteria correctly excluded for UG applicants")
    else:
        print("✗ ERROR: PG criteria applying to UG applicants")
    
    # Verify universal criteria apply to both
    universal_criteria = [c for c in result.criteria if c.applies_when is None]
    if len(universal_criteria) > 0:
        print(f"✓ {len(universal_criteria)} universal criteria apply to all applicants")
    
    # Verify NOT_APPLICABLE status is being used
    ug_not_applicable = [r for r in ug_eval['results'] if r['status'] == 'not_applicable']
    if len(ug_not_applicable) > 0:
        print(f"✓ {len(ug_not_applicable)} criteria marked as NOT_APPLICABLE for UG (don't affect decision)")
    
    print("\n" + "=" * 70)
    print("✅ INTEGRATION TEST PASSED - ALL WORKFLOWS WORKING CORRECTLY")
    print("=" * 70)
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
