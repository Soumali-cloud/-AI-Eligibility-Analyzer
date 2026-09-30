import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import ExtractedEligibility


load_dotenv()


# ============================================================
# OPENAI CONFIGURATION
# ============================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.4-mini",
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not configured. "
        "Add it to backend/.env"
    )


client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """

You are an expert eligibility-policy extraction system.

You analyze webpages belonging to:

- Government scholarships
- Government welfare schemes
- Education schemes
- Bank schemes
- NGO scholarships
- Private scholarships
- Public-benefit programs

Your output will be consumed by a deterministic eligibility
engine.

Therefore:

ACCURACY > COMPLETENESS > CREATIVITY.

NEVER invent an eligibility requirement.

NEVER assume a requirement that is not supported by the
provided source.

NEVER decide whether a hypothetical applicant is eligible.

Your task is to extract eligibility rules and represent them
in a machine-readable form.


============================================================
WHAT COUNTS AS AN ELIGIBILITY CRITERION?
============================================================

Extract requirements concerning things such as:

- Age
- Academic marks
- Percentage
- CGPA
- Income
- Family income
- Residence
- State
- District
- Citizenship
- Category
- Gender where explicitly stated
- Disability status
- Education level
- Course
- Institution
- Year of study
- Admission status
- Employment status
- Occupation
- Family circumstances
- Parent/guardian circumstances
- Bank/account requirements when they determine eligibility
- Application type when it determines eligibility
- Course type
- Academic session
- Drop-year conditions
- Other explicit eligibility requirements


============================================================
IMPORTANT DISTINCTION
============================================================

Do NOT treat every piece of information on a webpage as an
eligibility criterion.

For example:

"Applications are open from July 1."

is an application note, NOT necessarily an eligibility
criterion.

"Applicants must be residents of West Bengal."

is an eligibility criterion.

"Applicants must have at least 60% marks."

is an eligibility criterion.

"Applicants must submit an income certificate."

is primarily a required document.

However, if possessing the document itself is explicitly stated
as a condition of eligibility, preserve that relationship.


============================================================
EXTRACT ALL SUPPORTED CRITERIA
============================================================

Do NOT extract only numerical criteria.

Categorical and textual requirements are equally important.

Example:

"Students pursuing undergraduate courses are eligible."

Extract:

category = education
data_type = select
operator = in
options = ["undergraduate"]


Example:

"Applicants must be residents of West Bengal."

Extract:

category = residence
data_type = select
operator = in
options = ["West Bengal"]


Example:

"Only fresh applicants are eligible."

Extract:

category = application_type
data_type = select
operator = in
options = ["Fresh"]


============================================================
NUMERICAL RULES
============================================================

Example:

"Applicants must have secured at least 75%."

Extract:

category = academic_performance
data_type = percentage
operator = >=
value = "75"
minimum = 75
unit = "percent"


Example:

"Annual family income should not exceed Rs. 3 lakh."

Extract:

category = income
data_type = currency
operator = <=
value = "300000"
maximum = 300000
unit = "INR"


Example:

"Applicants must be between 18 and 25 years."

Extract:

category = age
data_type = number
operator = between
minimum = 18
maximum = 25
unit = "years"


============================================================
CONDITIONAL RULES & APPLICABILITY CONDITIONS
============================================================

Preserve conditional relationships.

Example:

"Undergraduate students must have at least 60% marks."

This should be extracted as:

name = "Academic Performance - Undergraduate"
category = academic_performance
operator = >=
value = "60"
conditional = true

applies_when:
    field = education_level
    operator = equals
    value = undergraduate


Example:

"Postgraduate students must have at least 53% marks."

Extract separately:

name = "Academic Performance - Postgraduate"
category = academic_performance
operator = >=
value = "53"
conditional = true

applies_when:
    field = education_level
    operator = equals
    value = postgraduate


Example:

"Renewal applicants enrolled in postgraduate courses must have
at least 65% marks."

Extract:

applies_when:
    all:
        - field = application_type
          operator = equals
          value = renewal

        - field = education_level
          operator = equals
          value = postgraduate


============================================================
IMPORTANT: KEEP ALL VARIANTS
============================================================

Do NOT collapse different education levels into one criterion.

WRONG:

One generic "Academic Performance" criterion.

CORRECT:

- Academic Performance - Undergraduate
- Academic Performance - Postgraduate
- Academic Performance - PhD

Each should retain its own applicability condition when
supported by the source.


Do NOT flatten conditional criteria into universal requirements.


============================================================
MULTIPLE CONDITIONS
============================================================

If a rule requires multiple conditions simultaneously, use "all".

Example:

A requirement applies only to:

Postgraduate students AND Renewal applicants.

Use:

applies_when:
    all:
        - education_level = postgraduate
        - application_type = renewal


If at least one condition can trigger the rule, use "any".

Do NOT silently convert OR into AND.


============================================================
APPLICABILITY FIELDS
============================================================

Every criterion MAY have an applies_when field.

If:

applies_when = null

the criterion is universal.

If applies_when contains a condition, preserve that condition.

Supported fields may include:

- education_level
- course
- course_type
- application_type
- applicant_category
- academic_session
- institution
- state
- residence
- gender
- disability_status
- year_of_study
- other source-supported applicant attributes


============================================================
SOURCE TRACEABILITY
============================================================

Every extracted criterion MUST contain source_text.

source_text should contain the exact or near-exact wording from
the webpage supporting the criterion.

Do not fabricate source wording.


============================================================
REQUIRED DOCUMENTS
============================================================

Extract documents separately.

Each document should include:

1. name
2. description if supported
3. mandatory
4. applies_when if the document is conditional
5. source_text

Example:

"Undergraduate applicants must submit admission receipt."

Document:

name = "Admission Receipt"
mandatory = true

applies_when:
    field = education_level
    operator = equals
    value = undergraduate

source_text =
"Undergraduate applicants must submit admission receipt"


If a document is universal:

applies_when = null


Do NOT collapse different document requirements.

Do NOT lose applicability conditions on documents.


============================================================
DEADLINES
============================================================

Extract application deadlines only when explicitly supported
by the source.

Do not infer deadlines.


============================================================
MULTI-PAGE SOURCE RULE
============================================================

The supplied content may contain information from multiple
official pages of the same website.

Treat those pages as part of the same official source.

If one page gives general scheme information and another
official page gives detailed eligibility requirements, use the
detailed page.

Do NOT assume that the homepage contains all eligibility rules.


============================================================
SOURCE PRIORITY
============================================================

When the same criterion appears on multiple official pages:

1. Prefer the most specific eligibility/guideline page.
2. Prefer official guideline/FAQ/eligibility pages over
   navigation pages.
3. Preserve the strongest directly supported wording.
4. Do not combine contradictory values without mentioning the
   contradiction in ambiguities.


============================================================
ZERO-CRITERIA RULE
============================================================

Returning zero criteria is acceptable ONLY when the supplied
source genuinely contains no identifiable eligibility
requirements.

If the source contains explicit eligibility language, extract
the supported criteria.


============================================================
MOST IMPORTANT DISPLAY RULE
============================================================

The extracted eligibility object represents the COMPLETE POLICY.

Therefore:

ALL supported criteria MUST remain in the "criteria" array.

This includes:

- universal criteria
- undergraduate criteria
- postgraduate criteria
- school criteria
- diploma criteria
- engineering criteria
- medical criteria
- M.Phil criteria
- Ph.D. criteria
- Kanyashree criteria
- Board Topper criteria
- fresh application criteria
- renewal criteria
- category-specific criteria
- course-specific criteria
- drop-year criteria
- conditional criteria

A criterion MUST NOT be removed merely because it is conditional.

A criterion MUST NOT be removed merely because it does not apply
to every applicant.

A criterion MUST NOT be converted into a universal rule merely
because its applicability is conditional.

Use applies_when to preserve the condition.


============================================================
DISPLAY VS APPLICANT QUESTIONS
============================================================

This is a critical architectural distinction.

The analysis page will display ALL extracted policy rules.

Later, the applicant-specific questionnaire will use
applies_when to determine which rules require user input.

Therefore:

POLICY EXTRACTION
    =
ALL RULES

APPLICABILITY
    =
WHICH RULES APPLY TO THIS APPLICANT

ELIGIBILITY ENGINE
    =
WHETHER THE APPLICANT SATISFIES THOSE APPLICABLE RULES


============================================================
FINAL RULE
============================================================

Do not invent.

Do not guess.

Do not make an eligibility decision.

Extract the complete supported policy faithfully.

Preserve separate applicant pathways.

Preserve applicability conditions.

Preserve source evidence.

The goal is to reconstruct the eligibility policy as completely
as the supplied official source allows.

"""


# ============================================================
# BUILD STRUCTURED SOURCE
# ============================================================

def build_source_text(
    page_data: Dict,
) -> str:
    """
    Build a compact but information-preserving representation
    of the scraped source.

    Important:
    - Preserve structured information.
    - Preserve discovered official pages.
    - Avoid adding full_text when it duplicates the structured
      content.
    """

    sections = []

    # ---------------------------------------------------------
    # BASIC PAGE INFORMATION
    # ---------------------------------------------------------

    title = page_data.get(
        "title",
        "",
    )

    description = page_data.get(
        "description",
        "",
    )

    if title:
        sections.append(
            f"PAGE TITLE:\n{title}"
        )

    if description:
        sections.append(
            f"PAGE DESCRIPTION:\n{description}"
        )

    # ---------------------------------------------------------
    # HEADINGS
    # ---------------------------------------------------------

    headings = page_data.get(
        "headings",
        [],
    )

    if headings:
        sections.append(
            "HEADINGS:\n"
            + "\n".join(
                f"- {heading}"
                for heading in headings
            )
        )

    # ---------------------------------------------------------
    # PARAGRAPHS
    # ---------------------------------------------------------

    paragraphs = page_data.get(
        "paragraphs",
        [],
    )

    if paragraphs:
        sections.append(
            "PARAGRAPHS:\n"
            + "\n".join(
                f"- {paragraph}"
                for paragraph in paragraphs
            )
        )

    # ---------------------------------------------------------
    # LIST ITEMS
    # ---------------------------------------------------------

    lists = page_data.get(
        "lists",
        [],
    )

    if lists:
        sections.append(
            "LIST ITEMS:\n"
            + "\n".join(
                f"- {item}"
                for item in lists
            )
        )

    # ---------------------------------------------------------
    # TABLES
    # ---------------------------------------------------------

    tables = page_data.get(
        "tables",
        [],
    )

    if tables:

        table_text = []

        for table_index, table in enumerate(
            tables,
            start=1,
        ):

            table_text.append(
                f"TABLE {table_index}:"
            )

            for row in table:

                row_text = " | ".join(
                    str(cell)
                    for cell in row
                ).strip()

                if row_text:
                    table_text.append(
                        row_text
                    )

        if table_text:
            sections.append(
                "TABLE DATA:\n"
                + "\n".join(table_text)
            )

    # ---------------------------------------------------------
    # DISCOVERED OFFICIAL PAGES
    # ---------------------------------------------------------

    discovered_pages = page_data.get(
        "discovered_pages",
        [],
    )

    if discovered_pages:

        discovered_text = [
            "DISCOVERED OFFICIAL SOURCE PAGES:"
        ]

        for page in discovered_pages:

            page_title = page.get(
                "title",
                "",
            )

            page_url = page.get(
                "url",
                "",
            )

            page_text = page.get(
                "text",
                "",
            )

            if page_title or page_url:
                discovered_text.append(
                    f"- {page_title} ({page_url})"
                )

            if page_text:
                discovered_text.append(
                    page_text
                )

        sections.append(
            "\n".join(
                discovered_text
            )
        )

    # ---------------------------------------------------------
    # FULL TEXT FALLBACK
    # ---------------------------------------------------------
    #
    # Do NOT add full_text when structured content already exists.
    # That would duplicate a large amount of information.

    full_text = page_data.get(
        "full_text",
        "",
    )

    has_structured_content = any(
        [
            headings,
            paragraphs,
            lists,
            tables,
            discovered_pages,
        ]
    )

    if (
        full_text
        and not has_structured_content
    ):
        sections.append(
            "FULL SOURCE TEXT:\n"
            + full_text
        )

    return "\n\n".join(
        sections
    )


# ============================================================
# FIND ELIGIBILITY-RELATED CONTENT
# ============================================================

def build_relevant_text(
    page_data: Dict,
) -> str:
    """
    Build focused eligibility evidence while preserving nearby
    context.

    Instead of selecting only isolated keyword lines, nearby
    content is included so that relationships between headings,
    applicant groups, requirements and conditions are preserved.
    """

    keywords = [
        "eligib",
        "criteria",
        "eligible",
        "applicant",
        "student",
        "candidate",
        "income",
        "family",
        "marks",
        "percentage",
        "cgpa",
        "age",
        "residen",
        "domicile",
        "course",
        "education",
        "qualification",
        "category",
        "caste",
        "disab",
        "annual",
        "require",
        "condition",
        "fresh",
        "renewal",
        "session",
        "admission",
        "merit",
        "scholarship",
        "engineering",
        "medical",
        "postgraduate",
        "undergraduate",
        "diploma",
        "phd",
        "mphil",
        "kanyashree",
        "topper",
        "drop",
        "document",
        "certificate",
    ]

    blocks = []

    def add_block(
        text: str,
    ):
        text = str(
            text
        ).strip()

        if not text:
            return

        lower = text.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):

            if text not in blocks:
                blocks.append(
                    text
                )

    # ---------------------------------------------------------
    # HEADINGS
    # ---------------------------------------------------------

    for heading in page_data.get(
        "headings",
        [],
    ):
        add_block(
            heading
        )

    # ---------------------------------------------------------
    # PARAGRAPHS
    # ---------------------------------------------------------

    paragraphs = page_data.get(
        "paragraphs",
        [],
    )

    for index, paragraph in enumerate(
        paragraphs
    ):

        paragraph_text = str(
            paragraph
        ).strip()

        if not paragraph_text:
            continue

        lower = paragraph_text.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):

            start = max(
                0,
                index - 1,
            )

            end = min(
                len(paragraphs),
                index + 2,
            )

            for nearby in paragraphs[
                start:end
            ]:
                add_block(
                    nearby
                )

    # ---------------------------------------------------------
    # LIST ITEMS
    # ---------------------------------------------------------

    lists = page_data.get(
        "lists",
        [],
    )

    for index, item in enumerate(
        lists
    ):

        item_text = str(
            item
        ).strip()

        if not item_text:
            continue

        lower = item_text.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):

            start = max(
                0,
                index - 1,
            )

            end = min(
                len(lists),
                index + 2,
            )

            for nearby in lists[
                start:end
            ]:
                add_block(
                    nearby
                )

    # ---------------------------------------------------------
    # TABLES
    # ---------------------------------------------------------

    for table in page_data.get(
        "tables",
        [],
    ):

        for row in table:

            row_text = " | ".join(
                str(cell)
                for cell in row
            ).strip()

            add_block(
                row_text
            )

    # ---------------------------------------------------------
    # DISCOVERED OFFICIAL PAGES
    # ---------------------------------------------------------

    for page in page_data.get(
        "discovered_pages",
        [],
    ):

        page_title = page.get(
            "title",
            "",
        )

        page_url = page.get(
            "url",
            "",
        )

        page_text = page.get(
            "text",
            "",
        )

        if page_title:

            page_header = (
                f"[OFFICIAL PAGE] "
                f"{page_title} "
                f"({page_url})"
            )

            if page_header not in blocks:
                blocks.append(
                    page_header
                )

        if page_text:

            lines = page_text.split(
                "\n"
            )

            for index, line in enumerate(
                lines
            ):

                line = line.strip()

                if not line:
                    continue

                lower = line.lower()

                if any(
                    keyword in lower
                    for keyword in keywords
                ):

                    start = max(
                        0,
                        index - 1,
                    )

                    end = min(
                        len(lines),
                        index + 2,
                    )

                    for nearby in lines[
                        start:end
                    ]:

                        nearby = nearby.strip()

                        if (
                            nearby
                            and nearby not in blocks
                        ):
                            blocks.append(
                                nearby
                            )

    return "\n".join(
        blocks
    )


# ============================================================
# AI EXTRACTION
# ============================================================

def extract_eligibility_with_ai(
    page_data: Dict,
) -> ExtractedEligibility:
    """
    Use OpenAI structured output to extract complete eligibility
    information from the scraped source.
    """

    full_text = page_data.get(
        "full_text",
        "",
    )

    if not full_text.strip():
        raise RuntimeError(
            "No readable text was extracted "
            "from the webpage."
        )

    # ---------------------------------------------------------
    # BUILD STRUCTURED SOURCE
    # ---------------------------------------------------------

    structured_source = build_source_text(
        page_data
    )

    # Keep the request reasonably sized.
    #
    # The previous implementation allowed 60,000 characters
    # here and separately allowed another 25,000 characters
    # of focused evidence.
    #
    # We keep enough content for broad policy extraction while
    # preventing unnecessarily large requests.

    max_characters = 30000

    structured_source = structured_source[
        :max_characters
    ]

    # ---------------------------------------------------------
    # BUILD FOCUSED ELIGIBILITY CONTENT
    # ---------------------------------------------------------

    relevant_text = build_relevant_text(
        page_data
    )

    # Focused evidence is useful, but should not become another
    # huge duplicate source.

    if len(relevant_text) > 12000:

        relevant_text = relevant_text[
            :12000
        ]

    # ---------------------------------------------------------
    # USER PROMPT
    # ---------------------------------------------------------

    user_prompt = f"""
Analyze this scholarship or government/private scheme source.

SOURCE URL:
{page_data.get("url", "")}

MAIN PAGE TITLE:
{page_data.get("title", "")}


============================================================
FOCUSED ELIGIBILITY EVIDENCE
============================================================

{relevant_text if relevant_text else "[No focused eligibility evidence found]"}


============================================================
STRUCTURED OFFICIAL SOURCE
============================================================

{structured_source}


============================================================
TASK
============================================================

Extract the COMPLETE eligibility policy represented by the
supplied official source.

Preserve ALL distinct eligibility pathways.

Do NOT return only common or universal requirements.

If the source contains separate rules for:

- school students
- undergraduate students
- postgraduate students
- diploma students
- engineering students
- medical students
- M.Phil students
- Ph.D. students
- Kanyashree applicants
- Board Toppers
- fresh applicants
- renewal applicants
- different categories
- different courses
- different years
- drop-year applicants

then preserve those rules as separate criteria whenever the
source supports them.


============================================================
CRITICAL DISPLAY VS APPLICABILITY RULE
============================================================

The extracted result represents the COMPLETE POLICY.

Therefore ALL supported criteria must remain in:

criteria

even when they are conditional.

Conditional criteria must NOT disappear.

Conditional criteria must NOT be converted into universal rules.

Instead, preserve the condition in:

applies_when


Example:

UG percentage >= 60

applies_when:
    education_level = undergraduate


PG percentage >= 53

applies_when:
    education_level = postgraduate


Both criteria must remain in the extracted policy.


============================================================
UNIVERSAL RULES
============================================================

If a rule genuinely applies to everyone:

applies_when = null

Do not make a rule universal merely because the applicant group
is not immediately obvious.


============================================================
DOCUMENT REQUIREMENTS
============================================================

Extract ALL supported document requirements.

Do not discard conditional documents.

For example:

UG:
- Marksheet
- Admission receipt

PG:
- PG marksheet

PhD:
- Research proposal
- Registration document

All should remain in the policy model if supported by the source.

Preserve their applies_when conditions.


============================================================
MULTI-PAGE SOURCE
============================================================

The source may contain several official pages discovered from
the starting URL.

Treat all relevant official pages as evidence for the same
scheme.

If one page contains general information and another contains
detailed eligibility rules, preserve the detailed rules.

Do not assume that the starting homepage contains every rule.


============================================================
SOURCE TRACEABILITY
============================================================

Every criterion must contain source_text.

Every document requirement must contain source_text.

Do not fabricate source wording.


============================================================
NO ELIGIBILITY DECISION
============================================================

You are extracting policy rules only.

Do not determine whether an applicant is eligible.

The deterministic eligibility engine will make that decision
later.


============================================================
FINAL REQUIREMENT
============================================================

The output must represent the COMPLETE set of eligibility rules
supported by the supplied source.

The analysis page will display ALL of these rules.

The applicant questionnaire will later use applies_when to
determine which rules require user input.

Therefore:

ALL RULES
    ->
policy extraction and display

APPLICABILITY
    ->
applicant-specific questions

ELIGIBILITY ENGINE
    ->
final eligibility decision
"""


    # ---------------------------------------------------------
    # CALL OPENAI
    # ---------------------------------------------------------

    try:

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=user_prompt,
            text_format=ExtractedEligibility,
        )

        parsed = response.output_parsed

        if parsed is None:
            raise RuntimeError(
                "The AI did not return structured "
                "eligibility data."
            )

        return parsed

    except Exception as exc:

        raise RuntimeError(
            "AI eligibility extraction failed: "
            f"{exc}"
        ) from exc