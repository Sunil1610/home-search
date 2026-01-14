"""
Telugu term normalization for real estate transcripts.
Converts Telugu terms to standardized English equivalents.
"""

import re
from typing import Dict, Tuple

# Telugu real estate terminology mappings
TELUGU_TERMS: Dict[str, str] = {
    # Units of measurement
    "గజాలు": "sq_yards",
    "గజాల": "sq_yards",
    "గజం": "sq_yard",
    "అడుగులు": "sq_ft",
    "అడుగుల": "sq_ft",
    "చదరపు అడుగులు": "sq_ft",
    "చదరపు గజాలు": "sq_yards",

    # Price units
    "లక్షలు": "lakhs",
    "లక్షల": "lakhs",
    "లక్ష": "lakh",
    "కోట్లు": "crores",
    "కోటి": "crore",
    "రూపాయలు": "rupees",

    # Directions
    "తూర్పు": "east",
    "తూర్పు ముఖం": "east_facing",
    "పడమర": "west",
    "పడమర ముఖం": "west_facing",
    "ఉత్తరం": "north",
    "ఉత్తర ముఖం": "north_facing",
    "దక్షిణం": "south",
    "దక్షిణ ముఖం": "south_facing",

    # Property features
    "బోర్ వెల్": "bore_well",
    "బోర్": "bore_well",
    "సంప్": "sump",
    "ఓవర్ హెడ్ ట్యాంక్": "overhead_tank",
    "ఓవర్ హెడ్": "overhead_tank",
    "పూజ గది": "pooja_room",
    "పూజా రూమ్": "pooja_room",
    "కార్ పార్కింగ్": "car_parking",
    "బైక్ పార్కింగ్": "bike_parking",
    "టెర్రస్": "terrace",
    "సెల్లార్": "cellar",
    "బేస్మెంట్": "basement",
    "మోడ్యులర్ కిచెన్": "modular_kitchen",
    "గార్డెన్": "garden",

    # Room types
    "బెడ్ రూమ్": "bedroom",
    "బెడ్ రూమ్స్": "bedrooms",
    "బాత్ రూమ్": "bathroom",
    "బాత్ రూమ్స్": "bathrooms",
    "హాల్": "hall",
    "కిచెన్": "kitchen",
    "డైనింగ్": "dining",
    "లివింగ్ రూమ్": "living_room",
    "బాల్కనీ": "balcony",

    # Property types
    "ఇండిపెండెంట్ హౌస్": "independent_house",
    "డూప్లెక్స్": "duplex",
    "అపార్ట్మెంట్": "apartment",
    "ఫ్లాట్": "flat",
    "విల్లా": "villa",
    "ప్లాట్": "plot",
    "భూమి": "land",

    # Approvals
    "GHMC అప్రూవ్డ్": "GHMC_approved",
    "HMDA అప్రూవ్డ్": "HMDA_approved",
    "రిజిస్ట్రేషన్ రెడీ": "registration_ready",
    "బ్యాంక్ లోన్": "bank_loan",
    "లోన్ ఎలిజిబుల్": "loan_eligible",

    # Floors
    "గ్రౌండ్ ఫ్లోర్": "ground_floor",
    "ఫస్ట్ ఫ్లోర్": "first_floor",
    "సెకండ్ ఫ్లోర్": "second_floor",
    "థర్డ్ ఫ్లోర్": "third_floor",

    # Common terms
    "అమ్మకానికి": "for_sale",
    "అద్దెకు": "for_rent",
    "రెడీ టు మూవ్": "ready_to_move",
    "కొత్త ఇల్లు": "new_house",
    "పాత ఇల్లు": "old_house",
    "రోడ్ ఫేసింగ్": "road_facing",
    "కార్నర్ ప్లాట్": "corner_plot",
}

# Telugu numerals to Arabic
TELUGU_NUMERALS: Dict[str, str] = {
    "౦": "0", "౧": "1", "౨": "2", "౩": "3", "౪": "4",
    "౫": "5", "౬": "6", "౭": "7", "౮": "8", "౯": "9",
}

# Telugu number words
TELUGU_NUMBER_WORDS: Dict[str, int] = {
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
    "ఆరు": 6, "ఏడు": 7, "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10,
    "పదకొండు": 11, "పన్నెండు": 12, "పదమూడు": 13, "పద్నాలుగు": 14,
    "పదిహేను": 15, "పదహారు": 16, "పదిహేడు": 17, "పద్దెనిమిది": 18,
    "పంతొమ్మిది": 19, "ఇరవై": 20, "ముప్పై": 30, "నలభై": 40,
    "యాభై": 50, "అరవై": 60, "డెబ్బై": 70, "ఎనభై": 80,
    "తొంభై": 90, "వంద": 100, "నూరు": 100, "వెయ్యి": 1000,
}


def normalize_telugu_numerals(text: str) -> str:
    """Convert Telugu numerals to Arabic numerals."""
    for telugu, arabic in TELUGU_NUMERALS.items():
        text = text.replace(telugu, arabic)
    return text


def normalize_telugu_terms(text: str) -> str:
    """
    Replace Telugu real estate terms with English equivalents.

    Args:
        text: Text containing Telugu terms

    Returns:
        Text with Telugu terms replaced by English equivalents
    """
    # Sort by length (longest first) to avoid partial replacements
    sorted_terms = sorted(TELUGU_TERMS.items(), key=lambda x: len(x[0]), reverse=True)

    for telugu, english in sorted_terms:
        text = text.replace(telugu, english)

    return text


def normalize_number_words(text: str) -> str:
    """Convert Telugu number words to digits."""
    for word, num in TELUGU_NUMBER_WORDS.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(word) + r'\b'
        text = re.sub(pattern, str(num), text)
    return text


def extract_price_mentions(text: str) -> list:
    """
    Extract price mentions from text.

    Returns list of tuples: (amount, unit, original_text)
    """
    prices = []

    # Pattern for prices like "50 lakhs", "1.5 crores", "50 లక్షలు"
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(lakhs?|lakh|crores?|crore|లక్షలు|లక్షల|కోట్లు|కోటి)',
        r'(Rs\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            prices.append(match.group(0))

    return prices


def extract_dimensions(text: str) -> list:
    """
    Extract dimension mentions from text.

    Returns list of dimension strings found.
    """
    dimensions = []

    # Patterns for dimensions
    patterns = [
        r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',  # 30x40, 30 x 40
        r'(\d+(?:\.\d+)?)\s*(sq_yards?|sq_ft|గజాలు|అడుగులు|square\s*(?:yards?|feet?))',
        r'(\d+(?:\.\d+)?)\s*(yards?|feet?|ft)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            dimensions.append(match.group(0))

    return dimensions


def full_normalize(text: str) -> str:
    """
    Apply all normalizations to text.

    Args:
        text: Raw transcript text

    Returns:
        Normalized text with Telugu terms converted to English
    """
    # Step 1: Normalize Telugu numerals
    text = normalize_telugu_numerals(text)

    # Step 2: Normalize Telugu number words
    text = normalize_number_words(text)

    # Step 3: Normalize Telugu terms
    text = normalize_telugu_terms(text)

    # Step 4: Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def analyze_transcript(text: str) -> dict:
    """
    Analyze transcript and extract key information.

    Args:
        text: Transcript text (can be Telugu or mixed)

    Returns:
        Dictionary with extracted information
    """
    # Normalize first
    normalized = full_normalize(text)

    return {
        "original_length": len(text),
        "normalized_length": len(normalized),
        "normalized_text": normalized,
        "prices_found": extract_price_mentions(normalized),
        "dimensions_found": extract_dimensions(normalized),
        "has_telugu": any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in text),
    }


if __name__ == "__main__":
    # Test normalization
    test_texts = [
        "ఈ ప్రాపర్టీ 150 గజాలు, ధర 50 లక్షలు",
        "3BHK ఇండిపెండెంట్ హౌస్, తూర్పు ముఖం, బోర్ వెల్ ఉంది",
        "రెండు బెడ్ రూమ్స్, ఒకటి బాత్ రూమ్, కార్ పార్కింగ్",
        "GHMC అప్రూవ్డ్, బ్యాంక్ లోన్ ఎలిజిబుల్",
    ]

    print("=== Telugu Normalization Test ===\n")

    for text in test_texts:
        print(f"Original: {text}")
        normalized = full_normalize(text)
        print(f"Normalized: {normalized}")
        print()
