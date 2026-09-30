from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class URLAnalyzeRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="Scholarship or scheme webpage URL",
    )


class ExtractedPage(BaseModel):
    url: str
    title: str
    description: Optional[str] = None
    headings: List[str] = []
    paragraphs: List[str] = []
    lists: List[str] = []
    tables: List[List[str]] = []
    full_text: str


# ============================================================
# AI ELIGIBILITY SCHEMAS
# ============================================================


class ApplicabilityCondition(BaseModel):
    field: str = Field(
        ..., 
        description="User profile field that must match for the rule to apply.",
    )
    operator: Literal[
        "equals",
        "not_equals",
        "in",
        "contains",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
    ] = Field(
        default="equals",
        description="Comparison operator used for applicability evaluation.",
    )
    value: Optional[str] = Field(
        default=None,
        description="Expected value for the applicable condition.",
    )
    all: Optional[List["ApplicabilityCondition"]] = Field(
        default=None,
        description="All conditions in this list must match for the rule to apply.",
    )
    any: Optional[List["ApplicabilityCondition"]] = Field(
        default=None,
        description="At least one condition in this list must match for the rule to apply.",
    )
    not_: Optional["ApplicabilityCondition"] = Field(
        default=None,
        alias="not",
        description="Condition that must not match for the rule to apply.",
    )

    model_config = {
        "populate_by_name": True,
    }


class EligibilityCriterion(BaseModel):
    id: str = Field(
        description="Unique identifier such as age, annual_income, percentage"
    )

    name: str = Field(
        description="Human-readable criterion name"
    )

    category: str = Field(
        description=(
            "Category such as age, education, academic_performance, "
            "income, residence, category, institution, employment, "
            "documents, or other"
        )
    )

    description: str = Field(
        description="Human-readable explanation of the requirement"
    )

    data_type: str = Field(
        description=(
            "Expected user data type: number, currency, percentage, "
            "text, boolean, date, select, multi_select, or file"
        )
    )

    operator: Optional[str] = Field(
        default=None,
        description=(
            "Comparison operator such as >=, <=, =, !=, in, "
            "between, contains, or null when not applicable"
        )
    )

    value: Optional[str] = Field(
        default=None,
        description="Required value when applicable"
    )

    minimum: Optional[float] = Field(
        default=None,
        description="Minimum numeric value when applicable"
    )

    maximum: Optional[float] = Field(
        default=None,
        description="Maximum numeric value when applicable"
    )

    unit: Optional[str] = Field(
        default=None,
        description="Unit such as INR, percent, years, or null"
    )

    options: List[str] = Field(
        default_factory=list,
        description="Allowed options when the criterion is categorical"
    )

    mandatory: bool = Field(
        description="Whether this criterion is mandatory"
    )

    conditional: bool = Field(
        description="Whether this criterion applies only under certain conditions"
    )

    applies_when: Optional[ApplicabilityCondition] = Field(
        default=None,
        description=(
            "Structured applicability condition. A null value means the rule is universal."
        ),
    )

    condition_description: Optional[str] = Field(
        default=None,
        description="Explanation of when a conditional criterion applies"
    )

    source_text: str = Field(
        description=(
            "Exact or near-exact text from the webpage supporting "
            "this criterion"
        )
    )


class DocumentRequirement(BaseModel):
    name: str = Field(
        description="Name of the required document (e.g., 'Mark Sheet', 'Income Certificate')"
    )

    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the document requirement"
    )

    mandatory: bool = Field(
        default=True,
        description="Whether this document is mandatory or optional"
    )

    applies_when: Optional[ApplicabilityCondition] = Field(
        default=None,
        description=(
            "Structured applicability condition for this document. "
            "A null value means the document is universally required."
        ),
    )

    source_text: str = Field(
        description="Exact or near-exact text from the webpage supporting this requirement"
    )


class ExtractedEligibility(BaseModel):
    scheme_name: str = Field(
        description="Name of the scholarship or government/private scheme"
    )

    provider: Optional[str] = Field(
        default=None,
        description="Organization providing the scholarship or scheme"
    )

    summary: str = Field(
        description="Short explanation of what the scheme is"
    )

    criteria: List[EligibilityCriterion] = Field(
        default_factory=list,
        description="All identifiable eligibility criteria"
    )

    required_documents: List[DocumentRequirement] = Field(
        default_factory=list,
        description="Documents applicants are required to provide with optional applicability conditions"
    )

    application_deadline: Optional[str] = Field(
        default=None,
        description="Application deadline if clearly stated"
    )

    application_notes: List[str] = Field(
        default_factory=list,
        description="Important application-related notes"
    )

    ambiguities: List[str] = Field(
        default_factory=list,
        description=(
            "Eligibility statements that could not be interpreted "
            "with sufficient confidence"
        )
    )


class URLAnalyzeSource(BaseModel):
    url: str
    title: str


class URLAnalyzeResponse(BaseModel):
    success: bool
    message: str
    source: URLAnalyzeSource
    eligibility: ExtractedEligibility