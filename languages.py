REGIONAL_BASE = 0x1F1E6

# --- Language Constants ---
ENGLISH = "English"
FRENCH = "French"
SPANISH = "Spanish"
PORTUGUESE = "Portuguese"
GERMAN = "German"
SIMPLIFIED_CHINESE = "Simplified Chinese"
TRADITIONAL_CHINESE = "Traditional Chinese"
JAPANESE = "Japanese"
KOREAN = "Korean"
ITALIAN = "Italian"
DUTCH = "Dutch"
SWEDISH = "Swedish"
NORWEGIAN = "Norwegian"
DANISH = "Danish"
FINNISH = "Finnish"
POLISH = "Polish"
CZECH = "Czech"
SLOVAK = "Slovak"
HUNGARIAN = "Hungarian"
ROMANIAN = "Romanian"
BULGARIAN = "Bulgarian"
GREEK = "Greek"
TURKISH = "Turkish"
RUSSIAN = "Russian"
UKRAINIAN = "Ukrainian"
HEBREW = "Hebrew"
ARABIC = "Arabic"
THAI = "Thai"
VIETNAMESE = "Vietnamese"
HINDI = "Hindi"

# --- Country to Language Mapping ---
COUNTRY_LANGUAGE = {
    "US": ENGLISH, "GB": ENGLISH, "AU": ENGLISH,
    "CA": ENGLISH, "NZ": ENGLISH, "IE": ENGLISH,
    "FR": FRENCH, "BE": FRENCH, "CH": FRENCH,
    "ES": SPANISH, "MX": SPANISH, "AR": SPANISH,
    "CL": SPANISH, "CO": SPANISH, "PE": SPANISH,
    "PT": PORTUGUESE, "BR": PORTUGUESE,
    "DE": GERMAN, "AT": GERMAN,
    "CN": SIMPLIFIED_CHINESE,
    "SG": SIMPLIFIED_CHINESE,
    "TW": TRADITIONAL_CHINESE,
    "HK": TRADITIONAL_CHINESE,
    "JP": JAPANESE,
    "KR": KOREAN,
    "IT": ITALIAN,
    "NL": DUTCH,
    "SE": SWEDISH,
    "NO": NORWEGIAN,
    "DK": DANISH,
    "FI": FINNISH,
    "PL": POLISH,
    "CZ": CZECH,
    "SK": SLOVAK,
    "HU": HUNGARIAN,
    "RO": ROMANIAN,
    "BG": BULGARIAN,
    "GR": GREEK,
    "TR": TURKISH,
    "RU": RUSSIAN,
    "UA": UKRAINIAN,
    "IL": HEBREW,
    "SA": ARABIC, "AE": ARABIC, "EG": ARABIC,
    "TH": THAI,
    "VN": VIETNAMESE,
    "IN": HINDI,
}

def flag_to_country(flag):
    if len(flag) != 2:
        return None

    chars = []
    for c in flag:
        code = ord(c)
        if not (0x1F1E6 <= code <= 0x1F1FF):
            return None
        chars.append(chr(ord("A") + code - REGIONAL_BASE))

    return "".join(chars)

def language_from_flag(flag):
    country = flag_to_country(flag)
    if country is None:
        return None
    return COUNTRY_LANGUAGE.get(country)