REGIONAL_BASE = 0x1F1E6

COUNTRY_LANGUAGE = {
    "US": "English", "GB": "English", "AU": "English",
    "CA": "English", "NZ": "English", "IE": "English",
    "FR": "French", "BE": "French", "CH": "French",
    "ES": "Spanish", "MX": "Spanish", "AR": "Spanish",
    "CL": "Spanish", "CO": "Spanish", "PE": "Spanish",
    "PT": "Portuguese", "BR": "Portuguese",
    "DE": "German", "AT": "German",
    "CN": "Simplified Chinese",
    "SG": "Simplified Chinese",
    "TW": "Traditional Chinese",
    "HK": "Traditional Chinese",
    "JP": "Japanese",
    "KR": "Korean",
    "IT": "Italian",
    "NL": "Dutch",
    "SE": "Swedish",
    "NO": "Norwegian",
    "DK": "Danish",
    "FI": "Finnish",
    "PL": "Polish",
    "CZ": "Czech",
    "SK": "Slovak",
    "HU": "Hungarian",
    "RO": "Romanian",
    "BG": "Bulgarian",
    "GR": "Greek",
    "TR": "Turkish",
    "RU": "Russian",
    "UA": "Ukrainian",
    "IL": "Hebrew",
    "SA": "Arabic",
    "AE": "Arabic",
    "EG": "Arabic",
    "TH": "Thai",
    "VN": "Vietnamese",
    "IN": "Hindi",
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