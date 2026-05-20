"""Lookup tables for classifying Hindi location entities into state vs other.

Used by the HiNER → CitizenProfile converter to assign extracted LOC entities
to the right schema field (state / village_or_town / district).

Precedence in `classify_location()`:
  1. Major city match  → 'town'
  2. State / UT match  → 'state'
  3. Fallback         → 'district'

Cities are checked before states because some names appear in both contexts
(e.g., पटना, लखनऊ are both major cities AND district headquarters). Treating
them as towns is the safer default since the schema's `district` field is
already a free-text fallback.
"""

# Devanagari names of Indian states/UTs.
# Includes common variants and historical names.
INDIAN_STATES_HINDI: set[str] = {
    # States
    "उत्तर प्रदेश", "उत्तरप्रदेश",
    "बिहार",
    "महाराष्ट्र",
    "मध्य प्रदेश", "मध्यप्रदेश",
    "राजस्थान",
    "तमिल नाडु", "तमिलनाडु",
    "कर्नाटक",
    "गुजरात",
    "आंध्र प्रदेश", "आन्ध्र प्रदेश",
    "पश्चिम बंगाल", "पश्चिमी बंगाल",
    "तेलंगाना",
    "केरल",
    "ओडिशा", "ओड़िशा", "उड़ीसा",
    "हरियाणा",
    "पंजाब",
    "झारखंड",
    "असम",
    "छत्तीसगढ़",
    "उत्तराखंड",
    "हिमाचल प्रदेश",
    "त्रिपुरा",
    "मेघालय",
    "मणिपुर",
    "नागालैंड", "नागालैण्ड",
    "गोवा",
    "अरुणाचल प्रदेश",
    "मिज़ोरम", "मिजोरम",
    "सिक्किम",
    # Union Territories
    "दिल्ली", "नई दिल्ली",
    "जम्मू और कश्मीर", "जम्मू-कश्मीर",
    "लद्दाख",
    "चंडीगढ़", "चण्डीगढ़",
    "पुडुचेरी", "पांडिचेरी",
    "अंडमान और निकोबार", "अंडमान",
    "लक्षद्वीप",
    "दादरा और नगर हवेली", "दादरा एवं नगर हवेली",
}

# Common Indian major cities — used to classify as "town" rather than
# blindly defaulting to district. Add to this list as you encounter
# new cases in the data.
MAJOR_CITIES_HINDI: set[str] = {
    "मुंबई", "बंबई",
    "कोलकाता", "कलकत्ता",
    "चेन्नई", "मद्रास",
    "बैंगलोर", "बेंगलुरु",
    "हैदराबाद",
    "अहमदाबाद",
    "पुणे", "पूना",
    "जयपुर",
    "लखनऊ",
    "कानपुर",
    "नागपुर",
    "इंदौर",
    "भोपाल",
    "पटना",
    "गुवाहाटी",
    "रांची",
    "वाराणसी", "बनारस",
    "आगरा",
    "अमृतसर",
    "विशाखापत्तनम", "विशाखापट्टनम",
    "नासिक",
    "मेरठ",
    "फरीदाबाद",
    "गाजियाबाद",
    "लुधियाना",
    "सूरत",
    "वडोदरा", "बड़ोदरा",
    "रायपुर",
    "जोधपुर",
    "कोयंबटूर",
    "कोचीन", "कोच्चि",
    "तिरुवनंतपुरम", "त्रिवेंद्रम",
    "देहरादून",
    "गुड़गांव", "गुरुग्राम",
    "नोएडा",
    "धनबाद",
    "जमशेदपुर",
    "श्रीनगर",
    "ग्वालियर",
    "जबलपुर",
    "मधुबनी",
    "बीकानेर",
    "मंडला",
}


def classify_location(loc_text: str) -> str:
    """Returns one of: 'state', 'town', 'district'.

    Cities take precedence over states (some names like पटना, लखनऊ appear in
    both lists by way of being capital cities of their states); unknown
    locations fall back to 'district' as the conservative default.
    """
    text = loc_text.strip()
    if text in MAJOR_CITIES_HINDI:
        return "town"
    if text in INDIAN_STATES_HINDI:
        return "state"
    return "district"
