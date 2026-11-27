"""Small helpers about the learner's language.

These do not judge an explanation. They only pick which fixed phrase to use
before the language model has heard the learner, and read a plain yes or no.
"""

import re

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
}
_NO = {
    "no", "nope", "nah", "not", "nahi", "nahin", "na", "mat",
    "नहीं", "नही", "ना", "मत",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[\wऀ-ॿ]+", (text or "").lower())


def guess_language(text: str) -> str:
    """"hindi", "hinglish" or "english", from a short piece of text."""
    words = _words(text)
    if not words:
        return "hinglish"
    devanagari = sum(1 for word in words if re.search(r"[ऀ-ॿ]", word))
    roman_hindi = sum(1 for word in words if word in _ROMAN_HINDI)
    if devanagari == len(words):
        return "hindi"
    if devanagari or roman_hindi:
        return "hinglish"
    return "english"


def word_count(text: str) -> int:
    return len(_words(text))


def is_yes(text: str) -> bool:
    words = _words(text)
    return any(word in _YES for word in words) and not any(word in _NO for word in words)


def is_no(text: str) -> bool:
    return any(word in _NO for word in _words(text))
