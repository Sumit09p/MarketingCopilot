from pydantic import BaseModel, Field, HttpUrl, field_validator


class BrandProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=200)

    description: str = ""
    target_audience: str = ""
    products_services: list[str] = Field(default_factory=list)
    brand_tone: str = ""

    website: str = ""
    location: str = ""

    competitors: list[str] = Field(default_factory=list)
    social_links: dict[str, str] = Field(default_factory=dict)

    @field_validator("company_name", "industry")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value


class BrandProfileUpdate(BaseModel):
    company_name: str | None = None
    industry: str | None = None

    description: str | None = None
    target_audience: str | None = None
    products_services: list[str] | None = None
    brand_tone: str | None = None

    website: str | None = None
    location: str | None = None

    competitors: list[str] | None = None
    social_links: dict[str, str] | None = None


class BrandProfileResponse(BaseModel):
    id: str
    user_id: str

    company_name: str
    industry: str
    description: str

    target_audience: str
    products_services: list[str]

    brand_tone: str
    website: str
    location: str

    competitors: list[str]
    social_links: dict[str, str]

    created_at: object
    updated_at: object
    