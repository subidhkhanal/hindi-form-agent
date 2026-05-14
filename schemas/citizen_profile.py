"""CitizenProfile schema — target structure for Hindi-to-JSON extraction.

Used for fine-tuning Sarvam-1 to extract structured information from
self-descriptions provided in Hindi (government service centers, banking
KYC, scheme applications).

Design principles:
- All fields are Optional with default None. Real inputs are incomplete.
  The model must learn to leave fields null rather than hallucinate.
- Closed-set fields use Literal types to force the model to map free
  text into one of the allowed values.
- Government ID fields are booleans only — DO NOT capture actual ID
  numbers in training data (privacy by design).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CitizenProfile(BaseModel):
    # Personal identity
    full_name: Optional[str] = Field(
        None,
        description="Full name in Hindi or transliterated to Latin script"
    )
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[Literal["male", "female", "other"]] = None
    marital_status: Optional[Literal["single", "married", "widowed", "divorced"]] = None

    # Family
    father_or_husband_name: Optional[str] = Field(
        None,
        description="Father's or husband's name as commonly captured in Indian forms"
    )
    number_of_dependents: Optional[int] = Field(None, ge=0)

    # Location
    village_or_town: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")

    # Demographic / socioeconomic
    occupation: Optional[str] = None
    monthly_income_inr: Optional[int] = Field(None, ge=0)
    caste_category: Optional[Literal["general", "obc", "sc", "st"]] = None
    religion: Optional[str] = None

    # Government IDs (boolean only — do NOT store actual ID numbers)
    has_aadhaar: Optional[bool] = None
    has_pan: Optional[bool] = None
    has_voter_id: Optional[bool] = None
    has_ration_card: Optional[bool] = None

    # Banking
    has_bank_account: Optional[bool] = None
    bank_name: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "रमेश कुमार",
                "age": 35,
                "gender": "male",
                "marital_status": "married",
                "village_or_town": "मधुबनी",
                "district": "मधुबनी",
                "state": "बिहार",
                "occupation": "किसान",
                "has_aadhaar": True
            }
        }
    }
