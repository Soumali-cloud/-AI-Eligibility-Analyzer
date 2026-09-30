from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models.schemas import (
    URLAnalyzeRequest,
)

from app.services.extractor import (
    extract_eligibility_with_ai,
)

from app.services.scraper import (
    scrape_webpage,
)

from app.services.eligibility_engine import (
    evaluate_eligibility,
)


app = FastAPI(

    title="AI Eligibility Analyzer",

    description=(
        "Analyze scholarship and public-benefit "
        "webpages and evaluate eligibility."
    ),

    version="0.3.0",

)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173",

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "message":
            "AI Eligibility Analyzer API is running.",

        "version":
            "0.3.0",

    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():

    return {

        "status":
            "healthy",

    }


# ============================================================
# ANALYZE URL
# ============================================================

@app.post(
    "/api/analyze-url"
)
def analyze_url(
    request: URLAnalyzeRequest,
):

    try:

        # ----------------------------------------------------
        # Scrape webpage
        # ----------------------------------------------------

        page = scrape_webpage(
            str(request.url)
        )


        # ----------------------------------------------------
        # Extract eligibility using AI
        # ----------------------------------------------------

        eligibility = (
            extract_eligibility_with_ai(
                page
            )
        )


        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return {

            "success":
                True,

            "message":
                (
                    "Webpage analyzed and "
                    "eligibility criteria extracted "
                    "successfully."
                ),

            "source": {

                "url":
                    page["url"],

                "title":
                    page["title"],

            },

            "eligibility":
                eligibility.model_dump(),

        }


    except RuntimeError as exc:

        raise HTTPException(

            status_code=400,

            detail=str(exc),

        )


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                f"Unexpected error: {exc}"
            ),

        )


# ============================================================
# ELIGIBILITY REQUEST
# ============================================================

class EligibilityRequest(BaseModel):

    criteria: List[
        Dict[str, Any]
    ]

    user_data: Dict[
        str,
        Any
    ]


# ============================================================
# CHECK ELIGIBILITY
# ============================================================

@app.post(
    "/api/check-eligibility"
)
def check_eligibility(
    request: EligibilityRequest,
):

    try:

        result = evaluate_eligibility(

            criteria=
                request.criteria,

            user_data=
                request.user_data,

        )


        return {

            "success":
                True,

            "result":
                result,

        }


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Eligibility evaluation "
                f"failed: {exc}"
            ),

        )