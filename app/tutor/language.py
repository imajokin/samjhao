"""Small helpers about the learner's language.

These do not judge an explanation. They only pick which fixed phrase to use
before the language model has heard the learner, and read a plain yes or no.
"""

import re

# Where each script sits in Unicode.
_SCRIPTS = {
    "hindi": (0x0900, 0x097F),  # Devanagari
    "punjabi": (0x0A00, 0x0A7F),  # Gurmukhi
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
}

# The language codes Sarvam's speech-to-text reports.
_CODES = {
    "hi-IN": "hindi",
    "en-IN": "english",
    "pa-IN": "punjabi",
    "te-IN": "telugu",
    "kn-IN": "kannada",
}

# What we ask Sarvam's text-to-speech to speak.
SPEECH_CODES = {
    "hindi": "hi-IN",
    "hinglish": "hi-IN",
    "english": "en-IN",
    "punjabi": "pa-IN",
    "telugu": "te-IN",
    "kannada": "kn-IN",
}

# How the language is described to the language model.
PROMPT_NAMES = {
    "hindi": "Hindi",
    "hinglish": "Hindi mixed with English",
    "english": "English",
    "punjabi": "Punjabi",
    "telugu": "Telugu",
    "kannada": "Kannada",
}

# Common Hindi words as they appear when Hindi is typed in Latin letters.
_ROMAN_HINDI = {
    "hai", "hain", "ka", "ki", "ke", "ko", "mein", "aur", "kya", "kyun",
    "kyunki", "nahi", "nahin", "haan", "hota", "hoti", "hote", "wala", "se",
    "par", "yeh", "woh", "toh", "bhi", "kaise", "samjhao", "batao",
}

_YES = {
    "yes", "yeah", "yep", "ya", "ok", "okay", "right", "correct", "sure",
    "haan", "han", "ha", "haa", "ji", "sahi", "theek", "thik", "bilkul",
    "हाँ", "हां", "हा", "जी", "सही", "ठीक", "बिल्कुल",
    "ਹਾਂ", "ਜੀ", "ਸਹੀ", "ਠੀਕ", "ਬਿਲਕੁਲ",
    "అవును", "సరే", "avunu", "sare",
    "ಹೌದು", "ಸರಿ", "howdu", "haudu", "sari",
}
_NO = {
    "no", "nope", "nah", "not", "nahi", "nahin", "na", "mat",
    "नहीं", "नही", "ना", "मत",
    "ਨਹੀਂ", "ਨਾ",
    "కాదు", "లేదు", "వద్దు", "kaadu", "ledu",
    "ಇಲ್ಲ", "ಅಲ್ಲ", "ಬೇಡ", "illa", "alla",
}


def _words(text: str) -> list[str]:
    # Indian scripts use combining signs that \w alone does not cover.
    return re.findall(r"[\wऀ-ൿ]+", (text or "").lower())


def _script_of(word: str) -> str | None:
    for language, (low, high) in _SCRIPTS.items():
        if any(low <= ord(char) <= high for char in word):
            return language
    return None


def guess_language(text: str) -> str:
    """The learner's main language, from a short piece of text."""
    words = _words(text)
    if not words:
        return "hinglish"
    counts: dict[str, int] = {}
    for word in words:
        script = _script_of(word)
        if script:
            counts[script] = counts.get(script, 0) + 1
    if counts:
        language = max(counts, key=counts.get)
        if language == "hindi" and counts["hindi"] < len(words):
            return "hinglish"
        return language
    if any(word in _ROMAN_HINDI for word in words):
        return "hinglish"
    return "english"


def language_from_code(code: str, text: str = "") -> str:
    """The language for a speech-to-text language code, such as "pa-IN"."""
    language = _CODES.get((code or "").strip())
    if language in (None, "hindi", "english"):
        # Hindi and English are often mixed, so look at the words themselves.
        return guess_language(text) if text else (language or "hinglish")
    return language


def word_count(text: str) -> int:
    return len(_words(text))


def is_yes(text: str) -> bool:
    words = _words(text)
    return any(word in _YES for word in words) and not any(word in _NO for word in words)


def is_no(text: str) -> bool:
    return any(word in _NO for word in _words(text))


def quote_is_from(quote: str, spoken: list[str]) -> bool:
    """True if most of the quoted words really appear in what the learner said.

    This does not judge meaning; the language model does that. It only checks
    that a point marked "covered" can be traced to the learner's own words.
    """
    quoted = [word for word in _words(quote) if len(word) > 1]
    if not quoted:
        return False
    said = set()
    for line in spoken:
        said.update(_words(line))
    found = sum(1 for word in quoted if word in said)
    return found / len(quoted) >= 0.6
