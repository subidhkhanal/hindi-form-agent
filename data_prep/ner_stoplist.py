"""Common-noise stoplist for HiNER PER/LOC entities.

HiNER's annotation is known in the literature to mis-tag political party
names and common nouns as PERSON, and to truncate multi-word locations.
Any extracted entity whose surface form exactly matches an item in
NER_NOISE_STOPLIST is treated as noise — the entire training entry is
rejected by the converter.

Curate conservatively: an exact-match stoplist is safer than a substring
match because legitimate Indian names can contain these substrings.
"""

NER_NOISE_STOPLIST: set[str] = {
    # Political parties (HiNER often mistags as PER)
    "भाजपा", "कांग्रेस", "बीजेपी", "सपा", "बसपा", "आप", "टीएमसी",
    "एनसीपी", "जेडीयू", "आरजेडी", "डीएमके", "एआईएडीएमके",
    "शिवसेना", "अकाली", "जेएमएम",
    # Common Hindi nouns/adjectives mistagged as PER
    "विशेष", "गंभीर", "अदालत", "सरकार", "नेता", "मंत्री",
    "प्रधानमंत्री", "मुख्यमंत्री", "राष्ट्रपति", "अध्यक्ष",
    "पुलिस", "कोर्ट", "जज", "वकील", "आरोपी", "गवाह",
    # Common Hindi words mistagged as LOC
    "देश", "राज्य", "जिला", "गांव", "शहर", "नगर", "क्षेत्र",
}
