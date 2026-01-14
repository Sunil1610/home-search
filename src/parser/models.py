"""
Pydantic models for property data validation.
Defines the structure for extracted real estate information.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Dimensions(BaseModel):
    """Property dimensions."""
    length_ft: Optional[float] = None
    width_ft: Optional[float] = None
    plot_area_sq_yards: Optional[float] = None
    built_up_area_sq_ft: Optional[float] = None


class Price(BaseModel):
    """Property price information."""
    amount: Optional[int] = Field(None, description="Price in INR")
    price_per_sq_yard: Optional[int] = None
    negotiable: Optional[bool] = None


class Location(BaseModel):
    """Property location details."""
    area: Optional[str] = None
    sub_area: Optional[str] = None
    city: Optional[str] = Field(default="Hyderabad")
    state: Optional[str] = Field(default="Telangana")
    landmark: Optional[str] = None
    full_address: Optional[str] = None


class Configuration(BaseModel):
    """Property configuration (rooms, floors, etc.)."""
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floors: Optional[int] = None
    hall: Optional[bool] = None
    kitchen: Optional[bool] = None
    car_parking: Optional[bool] = None
    bike_parking: Optional[bool] = None


class Construction(BaseModel):
    """Construction details."""
    year_built: Optional[int] = None
    age_years: Optional[int] = None
    facing_direction: Optional[str] = None
    road_width_ft: Optional[float] = None
    construction_type: Optional[str] = None
    floors_allowed: Optional[str] = None


class Legal(BaseModel):
    """Legal and approval status."""
    ownership_type: Optional[str] = None
    approval_status: Optional[str] = None
    bank_loan_eligible: Optional[bool] = None


class Contact(BaseModel):
    """Contact information."""
    name: Optional[str] = None
    phone: Optional[List[str]] = None
    agency: Optional[str] = None
    role: Optional[str] = None


class PropertyData(BaseModel):
    """Complete property data extracted from transcript."""
    property_type: Optional[str] = Field(
        None,
        description="Type: independent_house, apartment, villa, plot, commercial"
    )
    dimensions: Optional[Dimensions] = None
    price: Optional[Price] = None
    location: Optional[Location] = None
    configuration: Optional[Configuration] = None
    amenities: Optional[List[str]] = Field(
        default_factory=list,
        description="List of amenities: bore_well, sump, pooja_room, etc."
    )
    construction: Optional[Construction] = None
    legal: Optional[Legal] = None
    contact: Optional[Contact] = None
    additional_notes: Optional[List[str]] = Field(
        default_factory=list,
        description="Any other relevant details"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="Extraction confidence 0.0-1.0"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return self.model_dump(exclude_none=True)


class ExtractionResult(BaseModel):
    """Result of property data extraction."""
    success: bool
    video_id: str
    property_data: Optional[PropertyData] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


# Example property data for testing
SAMPLE_PROPERTY = PropertyData(
    property_type="independent_house",
    dimensions=Dimensions(
        plot_area_sq_yards=150,
        built_up_area_sq_ft=2400
    ),
    price=Price(
        amount=12500000,
        price_per_sq_yard=83333,
        negotiable=True
    ),
    location=Location(
        area="LB Nagar",
        sub_area="Bairamalguda",
        city="Hyderabad"
    ),
    configuration=Configuration(
        bedrooms=3,
        bathrooms=3,
        floors=2,
        car_parking=True
    ),
    amenities=["bore_well", "sump", "pooja_room", "terrace"],
    construction=Construction(
        facing_direction="east",
        road_width_ft=30,
        approval_status="GHMC_approved"
    ),
    confidence_score=0.85
)


if __name__ == "__main__":
    # Test model
    print("=== Sample Property Data ===")
    print(SAMPLE_PROPERTY.model_dump_json(indent=2, exclude_none=True))
