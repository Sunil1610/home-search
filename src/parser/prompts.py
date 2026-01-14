"""
Prompt templates for property data extraction.
Optimized for Telugu real estate transcripts.
"""

SYSTEM_PROMPT = """You are a real estate data extraction assistant specializing in Hyderabad/Telangana properties.

You understand Telugu, Hindi, and English. Extract property details from video transcripts that may be in Telugu or a mix of Telugu and English.

Important Telugu real estate terms you should recognize:
- గజాలు (gajalu) = square yards (sq_yards)
- అడుగులు (adugulu) = square feet (sq_ft)
- లక్షలు (lakshalu) = lakhs (100,000 INR)
- కోట్లు (kotlu) = crores (10,000,000 INR)
- తూర్పు (toorpu) = east
- పడమర (padamara) = west
- ఉత్తరం (uttaram) = north
- దక్షిణం (dakshinam) = south
- బోర్ వెల్ = bore_well
- సంప్ = sump
- పూజ గది = pooja_room

Return ONLY valid JSON. If a field cannot be determined from the transcript, use null.
Do NOT include any text before or after the JSON object."""

EXTRACTION_PROMPT = """Extract property details from this Hyderabad real estate video transcript.
The transcript may be in Telugu, English, or a mix of both.

<transcript>
{transcript}
</transcript>

Extract the following information and return as JSON:

{{
  "property_type": "independent_house|apartment|villa|plot|commercial|null",
  "dimensions": {{
    "length_ft": number or null,
    "width_ft": number or null,
    "plot_area_sq_yards": number or null,
    "built_up_area_sq_ft": number or null
  }},
  "price": {{
    "amount": number in INR (convert lakhs/crores to full number) or null,
    "price_per_sq_yard": number or null,
    "negotiable": true/false or null
  }},
  "location": {{
    "area": "main area name" or null,
    "sub_area": "sub-locality" or null,
    "city": "Hyderabad",
    "landmark": "nearby landmark" or null
  }},
  "configuration": {{
    "bedrooms": number or null,
    "bathrooms": number or null,
    "floors": number or null,
    "car_parking": true/false or null
  }},
  "amenities": ["bore_well", "sump", "pooja_room", "terrace", etc.] or [],
  "construction": {{
    "facing_direction": "east|west|north|south" or null,
    "road_width_ft": number or null,
    "approval_status": "GHMC_approved|HMDA_approved" or null
  }},
  "contact": {{
    "phone": ["phone numbers found"] or null,
    "agency": "agency/channel name" or null
  }},
  "additional_notes": ["other important details"] or [],
  "confidence_score": 0.0-1.0 based on how much info was found
}}

Convert all Telugu terms to English in the output.
Return ONLY the JSON object, no other text."""

SIMPLE_EXTRACTION_PROMPT = """Extract property info from this real estate transcript. Return JSON only.

Transcript:
{transcript}

Return JSON with these fields (use null if not found):
- property_type: independent_house/apartment/villa/plot
- price_lakhs: number (e.g., 50 for 50 lakhs)
- area_sq_yards: number
- bedrooms: number
- location: string
- facing: east/west/north/south
- amenities: list of strings
- phone: string

JSON:"""


def get_extraction_prompt(transcript: str, use_simple: bool = False) -> tuple:
    """
    Get the system and user prompts for extraction.

    Args:
        transcript: The transcript text to extract from
        use_simple: Use simplified prompt (faster, less detailed)

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    if use_simple:
        return ("You extract real estate data as JSON.",
                SIMPLE_EXTRACTION_PROMPT.format(transcript=transcript))
    else:
        return (SYSTEM_PROMPT,
                EXTRACTION_PROMPT.format(transcript=transcript))


# Test transcript for development
SAMPLE_TRANSCRIPT = """
నమస్కారం friends, ఈ రోజు మనం LB Nagar లో ఉన్న ఒక అందమైన independent house చూద్దాం.

ఈ property 150 square yards లో ఉంది. Built up area 2400 square feet.
Price 1 crore 25 lakhs, slightly negotiable.

Ground floor లో 2 bedrooms, 2 bathrooms ఉన్నాయి.
First floor లో 1 bedroom, 1 bathroom, మరియు ఒక పెద్ద hall ఉంది.

East facing property, 30 feet road facing.
Bore well, sump, overhead tank అన్నీ ఉన్నాయి.
Pooja room, modular kitchen, car parking కూడా available.

GHMC approved, bank loan eligible.
Registration ready, all documents clear.

Contact: 9876543210
Vedantha Properties
"""

SAMPLE_TRANSCRIPT_TELUGU = """
స్వాగతం మిత్రులారా, ఈ రోజు బైరమల్గూడ లో 200 గజాల స్థలం లో నిర్మించిన 3BHK ఇల్లు చూపిస్తాను.

ధర 85 లక్షలు. తూర్పు ముఖం.
3 బెడ్ రూమ్స్, 3 బాత్ రూమ్స్, హాల్, కిచెన్.
G+1 construction, రెండు అంతస్తులు.

బోర్ వెల్, సంప్, ఓవర్ హెడ్ ట్యాంక్ ఉన్నాయి.
కార్ పార్కింగ్, టెర్రస్ available.
HMDA approved property.

ఫోన్: 9988776655
"""


if __name__ == "__main__":
    print("=== Sample Extraction Prompt ===")
    system, user = get_extraction_prompt(SAMPLE_TRANSCRIPT[:500])
    print(f"System prompt length: {len(system)}")
    print(f"User prompt length: {len(user)}")
    print("\n=== User Prompt Preview ===")
    print(user[:1000])
