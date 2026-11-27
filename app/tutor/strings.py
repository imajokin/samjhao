"""Every fixed phrase Samjhao says, in Hindi and English (HANDOVER.md 6.5).

Hindi is in Devanagari with technical and everyday English words left in
Latin letters, the way learners read them in textbooks.
"""

STRINGS = {
    "home_open": (
        "आज क्या समझाओगे? Topic बोलो, और अपनी class बताओ।",
        "What will you explain today? Say the topic and your class.",
    ),
    "ask_level": ("कौन सी class में हो?", "Which class are you in?"),
    "narrow_topic": ("{subject} में कौन सा topic?", "Which topic in {subject}?"),
    "confirm_topic": ("तुमने {topic} कहा?", "Did you say {topic}?"),
    "start_explain": (
        "मुझे यह ऐसे समझाओ जैसे मैं तुम्हारा छोटा भाई हूँ। Mic दबाओ और बोलो।",
        "Explain this to me like I am your younger brother. Tap the mic and speak.",
    ),
    "correct": ("हाँ, बिल्कुल सही।", "Yes, exactly right."),
    "say_more": ("यहाँ थोड़ा और बताओ।", "Tell me a little more here."),
    "hint_prefix": ("एक छोटा hint:", "A small hint:"),
    "done": (
        "शाबाश, तुमने पूरा समझा दिया।",
        "Well done, you explained all of it.",
    ),
    # Used at the end when a hint or an explanation was needed, so that the
    # app never claims the learner explained everything alone.
    "done_with_help": (
        "बढ़िया कोशिश। चलो देखते हैं कौन से points तुमने खुद समझाए।",
        "Good effort. Let us see which points you explained on your own.",
    ),
    "not_heard": (
        "आवाज़ साफ़ नहीं आई। Phone पास लाकर फिर से बोलो।",
        "I could not hear clearly. Bring the phone closer and say it again.",
    ),
    "rerecord_button": ("गलत सुना? फिर से बोलो", "Heard it wrong? Say it again"),
    "confirm_word": ("तुमने {a} कहा या {b}?", "Did you say {a} or {b}?"),
    "off_topic": ("चलो वापस topic पर आते हैं।", "Let us come back to the topic."),
    "unsure_topic": (
        "इस topic पर मुझे पूरा भरोसा नहीं है। क्या हम {nearby} पर बात करें?",
        "I am not fully sure about this topic. Shall we talk about {nearby}?",
    ),
    "thinking": ("सोच रहा हूँ…", "Thinking…"),
    "new_topic_button": ("नया topic", "New topic"),
    "keys_missing": (
        "Keys set नहीं हैं, इसलिए Samjhao अभी सुन या जवाब नहीं दे सकता।",
        "Keys are not set, so Samjhao cannot listen or reply yet. "
        "Try the live demo or watch the video.",
    ),
    "service_down": (
        "अभी थोड़ी दिक्कत आ रही है। थोड़ी देर में फिर से कोशिश करो।",
        "Something is not working right now. Please try again in a little while.",
    ),
}


def say(key: str, lang: str = "hindi", **values: str) -> str:
    """One fixed phrase in the learner's language.

    `lang` is "hindi", "hinglish" or "english". Hinglish speakers get the
    Hindi phrase, which already keeps English words in English.
    """
    hindi, english = STRINGS[key]
    text = english if lang == "english" else hindi
    return text.format(**values) if values else text
