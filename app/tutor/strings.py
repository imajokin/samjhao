"""Every fixed phrase Samjhao says, in its five languages (HANDOVER.md 6.5).

Each Indian language is written in its own script, with technical and
everyday English words left in Latin letters, the way learners read them in
textbooks. Where a phrase depends on whether Samjhao's voice is male or
female, it is a pair: (male, female).

The Punjabi, Telugu and Kannada phrases still need a check by a native speaker.
"""

LANGUAGES = ("hindi", "english", "punjabi", "telugu", "kannada")

STRINGS = {
    "home_open": {
        "hindi": "आज क्या समझाओगे? Topic बोलो, और अपनी class बताओ।",
        "english": "What will you explain today? Say the topic and your class.",
        "punjabi": "ਅੱਜ ਕੀ ਸਮਝਾਓਗੇ? Topic ਬੋਲੋ, ਅਤੇ ਆਪਣੀ class ਦੱਸੋ।",
        "telugu": "ఈ రోజు ఏం వివరిస్తావు? Topic చెప్పు, నీ class కూడా చెప్పు.",
        "kannada": "ಇಂದು ಏನು ವಿವರಿಸುತ್ತೀಯ? Topic ಹೇಳು, ನಿನ್ನ class ಕೂಡ ಹೇಳು.",
    },
    "ask_level": {
        "hindi": "कौन सी class में हो?",
        "english": "Which class are you in?",
        "punjabi": "ਕਿਹੜੀ class ਵਿੱਚ ਹੋ?",
        "telugu": "నువ్వు ఏ class లో ఉన్నావు?",
        "kannada": "ನೀನು ಯಾವ class ನಲ್ಲಿ ಇದ್ದೀಯ?",
    },
    "narrow_topic": {
        "hindi": "{subject} में कौन सा topic?",
        "english": "Which topic in {subject}?",
        "punjabi": "{subject} ਵਿੱਚ ਕਿਹੜਾ topic?",
        "telugu": "{subject} లో ఏ topic?",
        "kannada": "{subject} ನಲ್ಲಿ ಯಾವ topic?",
    },
    "confirm_topic": {
        "hindi": "तुमने {topic} कहा?",
        "english": "Did you say {topic}?",
        "punjabi": "ਤੁਸੀਂ {topic} ਕਿਹਾ?",
        "telugu": "నువ్వు {topic} అన్నావా?",
        "kannada": "ನೀನು {topic} ಅಂದೆಯಾ?",
    },
    "start_explain": {
        "hindi": (
            "मुझे यह ऐसे समझाओ जैसे मैं तुम्हारा छोटा भाई हूँ। Mic दबाओ और बोलो।",
            "मुझे यह ऐसे समझाओ जैसे मैं तुम्हारी छोटी बहन हूँ। Mic दबाओ और बोलो।",
        ),
        "english": (
            "Explain this to me like I am your younger brother. Tap the mic and speak.",
            "Explain this to me like I am your younger sister. Tap the mic and speak.",
        ),
        "punjabi": (
            "ਮੈਨੂੰ ਇਹ ਇਸ ਤਰ੍ਹਾਂ ਸਮਝਾਓ ਜਿਵੇਂ ਮੈਂ ਤੁਹਾਡਾ ਛੋਟਾ ਭਰਾ ਹਾਂ। Mic ਦਬਾਓ ਅਤੇ ਬੋਲੋ।",
            "ਮੈਨੂੰ ਇਹ ਇਸ ਤਰ੍ਹਾਂ ਸਮਝਾਓ ਜਿਵੇਂ ਮੈਂ ਤੁਹਾਡੀ ਛੋਟੀ ਭੈਣ ਹਾਂ। Mic ਦਬਾਓ ਅਤੇ ਬੋਲੋ।",
        ),
        "telugu": (
            "నేను నీ తమ్ముడిని అనుకుని నాకు ఇది వివరించు. Mic నొక్కి మాట్లాడు.",
            "నేను నీ చెల్లెలిని అనుకుని నాకు ఇది వివరించు. Mic నొక్కి మాట్లాడు.",
        ),
        "kannada": (
            "ನಾನು ನಿನ್ನ ತಮ್ಮ ಎಂದುಕೊಂಡು ನನಗೆ ಇದನ್ನು ವಿವರಿಸು. Mic ಒತ್ತಿ ಮಾತಾಡು.",
            "ನಾನು ನಿನ್ನ ತಂಗಿ ಎಂದುಕೊಂಡು ನನಗೆ ಇದನ್ನು ವಿವರಿಸು. Mic ಒತ್ತಿ ಮಾತಾಡು.",
        ),
    },
    "correct": {
        "hindi": "हाँ, बिल्कुल सही।",
        "english": "Yes, exactly right.",
        "punjabi": "ਹਾਂ, ਬਿਲਕੁਲ ਸਹੀ।",
        "telugu": "అవును, సరిగ్గా చెప్పావు.",
        "kannada": "ಹೌದು, ಸರಿಯಾಗಿ ಹೇಳಿದೆ.",
    },
    "say_more": {
        "hindi": "यहाँ थोड़ा और बताओ।",
        "english": "Tell me a little more here.",
        "punjabi": "ਇੱਥੇ ਥੋੜ੍ਹਾ ਹੋਰ ਦੱਸੋ।",
        "telugu": "ఇక్కడ ఇంకొంచెం చెప్పు.",
        "kannada": "ಇಲ್ಲಿ ಸ್ವಲ್ಪ ಇನ್ನೂ ಹೇಳು.",
    },
    "hint_prefix": {
        "hindi": "एक छोटा hint:",
        "english": "A small hint:",
        "punjabi": "ਇੱਕ ਛੋਟਾ hint:",
        "telugu": "ఒక చిన్న hint:",
        "kannada": "ಒಂದು ಚಿಕ್ಕ hint:",
    },
    "done": {
        "hindi": "शाबाश, तुमने पूरा समझा दिया।",
        "english": "Well done, you explained all of it.",
        "punjabi": "ਸ਼ਾਬਾਸ਼, ਤੁਸੀਂ ਪੂਰਾ ਸਮਝਾ ਦਿੱਤਾ।",
        "telugu": "శభాష్, నువ్వు మొత్తం వివరించావు.",
        "kannada": "ಶಭಾಷ್, ನೀನು ಪೂರ್ತಿ ವಿವರಿಸಿದೆ.",
    },
    # Used at the end when a hint or an explanation was needed, so that the
    # app never claims the learner explained everything alone.
    "done_with_help": {
        "hindi": "बढ़िया कोशिश। चलो देखते हैं कौन से points तुमने खुद समझाए।",
        "english": "Good effort. Let us see which points you explained on your own.",
        "punjabi": "ਵਧੀਆ ਕੋਸ਼ਿਸ਼। ਆਓ ਵੇਖੀਏ ਕਿਹੜੇ points ਤੁਸੀਂ ਆਪ ਸਮਝਾਏ।",
        "telugu": "మంచి ప్రయత్నం. నువ్వు సొంతంగా ఏ points వివరించావో చూద్దాం.",
        "kannada": "ಒಳ್ಳೆಯ ಪ್ರಯತ್ನ. ನೀನೇ ಯಾವ points ವಿವರಿಸಿದೆ ಎಂದು ನೋಡೋಣ.",
    },
    # Said before the first hint: it is fine not to know, try once.
    "nudge_first": {
        "hindi": "कोई बात नहीं, यह सोचने वाली बात है। एक बार कोशिश करके देखो।",
        "english": "No problem, this one needs some thought. Give it one try.",
        "punjabi": "ਕੋਈ ਗੱਲ ਨਹੀਂ, ਇਹ ਸੋਚਣ ਵਾਲੀ ਗੱਲ ਹੈ। ਇੱਕ ਵਾਰ ਕੋਸ਼ਿਸ਼ ਕਰਕੇ ਵੇਖੋ।",
        "telugu": "పర్వాలేదు, ఇది ఆలోచించాల్సిన విషయం. ఒకసారి ప్రయత్నించి చూడు.",
        "kannada": "ಪರವಾಗಿಲ್ಲ, ಇದು ಯೋಚಿಸಬೇಕಾದ ವಿಷಯ. ಒಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ ನೋಡು.",
    },
    # Said before the second hint: do not give up yet.
    "nudge_again": {
        "hindi": "इतनी जल्दी हार मत मानो, तुम पास पहुँच रहे हो। बस एक बार और कोशिश करो।",
        "english": "Do not give up yet, you are getting close. Try just once more.",
        "punjabi": "ਇੰਨੀ ਛੇਤੀ ਹਾਰ ਨਾ ਮੰਨੋ, ਤੁਸੀਂ ਨੇੜੇ ਪਹੁੰਚ ਰਹੇ ਹੋ। ਬੱਸ ਇੱਕ ਵਾਰ ਹੋਰ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "telugu": "ఇంత త్వరగా వదిలేయకు, నువ్వు దగ్గరికి వస్తున్నావు. ఇంకొక్కసారి ప్రయత్నించు.",
        "kannada": "ಇಷ್ಟು ಬೇಗ ಬಿಟ್ಟುಕೊಡಬೇಡ, ನೀನು ಹತ್ತಿರ ಬರುತ್ತಿದ್ದೀಯ. ಇನ್ನೊಮ್ಮೆ ಮಾತ್ರ ಪ್ರಯತ್ನಿಸು.",
    },
    # Said when both hints are used and the app explains the point itself.
    "explain_lead": {
        "hindi": (
            "तुमने अच्छी कोशिश की। यह वाला मैं समझा देता हूँ।",
            "तुमने अच्छी कोशिश की। यह वाला मैं समझा देती हूँ।",
        ),
        "english": "You tried well. Let me explain this one.",
        "punjabi": (
            "ਤੁਸੀਂ ਚੰਗੀ ਕੋਸ਼ਿਸ਼ ਕੀਤੀ। ਇਹ ਵਾਲਾ ਮੈਂ ਸਮਝਾ ਦਿੰਦਾ ਹਾਂ।",
            "ਤੁਸੀਂ ਚੰਗੀ ਕੋਸ਼ਿਸ਼ ਕੀਤੀ। ਇਹ ਵਾਲਾ ਮੈਂ ਸਮਝਾ ਦਿੰਦੀ ਹਾਂ।",
        ),
        "telugu": "నువ్వు బాగా ప్రయత్నించావు. ఇది నేను వివరిస్తాను.",
        "kannada": "ನೀನು ಚೆನ್ನಾಗಿ ಪ್ರಯತ್ನಿಸಿದೆ. ಇದನ್ನು ನಾನು ವಿವರಿಸುತ್ತೇನೆ.",
    },
    "give_up_button": {
        "hindi": "मुझे नहीं पता",
        "english": "I don't know",
        "punjabi": "ਮੈਨੂੰ ਨਹੀਂ ਪਤਾ",
        "telugu": "నాకు తెలియదు",
        "kannada": "ನನಗೆ ಗೊತ್ತಿಲ್ಲ",
    },
    "not_heard": {
        "hindi": "आवाज़ साफ़ नहीं आई। Phone पास लाकर फिर से बोलो।",
        "english": "I could not hear clearly. Bring the phone closer and say it again.",
        "punjabi": "ਆਵਾਜ਼ ਸਾਫ਼ ਨਹੀਂ ਆਈ। Phone ਨੇੜੇ ਲਿਆ ਕੇ ਫਿਰ ਬੋਲੋ।",
        "telugu": "మాట స్పష్టంగా వినిపించలేదు. Phone దగ్గరగా పెట్టి మళ్ళీ చెప్పు.",
        "kannada": "ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. Phone ಹತ್ತಿರ ಹಿಡಿದು ಮತ್ತೆ ಹೇಳು.",
    },
    "rerecord_button": {
        "hindi": "गलत सुना? फिर से बोलो",
        "english": "Heard it wrong? Say it again",
        "punjabi": "ਗਲਤ ਸੁਣਿਆ? ਫਿਰ ਬੋਲੋ",
        "telugu": "తప్పుగా విన్నానా? మళ్ళీ చెప్పు",
        "kannada": "ತಪ್ಪಾಗಿ ಕೇಳಿಸಿತಾ? ಮತ್ತೆ ಹೇಳು",
    },
    "confirm_word": {
        "hindi": "तुमने {a} कहा या {b}?",
        "english": "Did you say {a} or {b}?",
        "punjabi": "ਤੁਸੀਂ {a} ਕਿਹਾ ਜਾਂ {b}?",
        "telugu": "నువ్వు {a} అన్నావా, {b} అన్నావా?",
        "kannada": "ನೀನು {a} ಅಂದೆಯಾ ಅಥವಾ {b} ಅಂದೆಯಾ?",
    },
    "off_topic": {
        "hindi": "चलो वापस topic पर आते हैं।",
        "english": "Let us come back to the topic.",
        "punjabi": "ਚਲੋ ਵਾਪਸ topic ਉੱਤੇ ਆਉਂਦੇ ਹਾਂ।",
        "telugu": "మళ్ళీ topic కి వద్దాం.",
        "kannada": "ಮತ್ತೆ topic ಗೆ ಬರೋಣ.",
    },
    "unsure_topic": {
        "hindi": "इस topic पर मुझे पूरा भरोसा नहीं है। क्या हम {nearby} पर बात करें?",
        "english": "I am not fully sure about this topic. Shall we talk about {nearby}?",
        "punjabi": "ਇਸ topic ਬਾਰੇ ਮੈਨੂੰ ਪੂਰਾ ਭਰੋਸਾ ਨਹੀਂ ਹੈ। ਕੀ ਅਸੀਂ {nearby} ਬਾਰੇ ਗੱਲ ਕਰੀਏ?",
        "telugu": "ఈ topic మీద నాకు పూర్తి నమ్మకం లేదు. మనం {nearby} గురించి మాట్లాడదామా?",
        "kannada": "ಈ topic ಬಗ್ಗೆ ನನಗೆ ಪೂರ್ತಿ ಖಾತ್ರಿ ಇಲ್ಲ. ನಾವು {nearby} ಬಗ್ಗೆ ಮಾತಾಡೋಣವಾ?",
    },
    "thinking": {
        "hindi": ("सोच रहा हूँ…", "सोच रही हूँ…"),
        "english": "Thinking…",
        "punjabi": ("ਸੋਚ ਰਿਹਾ ਹਾਂ…", "ਸੋਚ ਰਹੀ ਹਾਂ…"),
        "telugu": "ఆలోచిస్తున్నాను…",
        "kannada": "ಯೋಚಿಸುತ್ತಿದ್ದೇನೆ…",
    },
    "new_topic_button": {
        "hindi": "नया topic",
        "english": "New topic",
        "punjabi": "ਨਵਾਂ topic",
        "telugu": "కొత్త topic",
        "kannada": "ಹೊಸ topic",
    },
    "keys_missing": {
        "hindi": "Keys set नहीं हैं, इसलिए Samjhao अभी सुन या जवाब नहीं दे सकता।",
        "english": "Keys are not set, so Samjhao cannot listen or reply yet. "
        "Try the live demo or watch the video.",
    },
    "service_down": {
        "hindi": "अभी थोड़ी दिक्कत आ रही है। थोड़ी देर में फिर से कोशिश करो।",
        "english": "Something is not working right now. Please try again in a little while.",
        "punjabi": "ਹੁਣੇ ਥੋੜ੍ਹੀ ਦਿੱਕਤ ਆ ਰਹੀ ਹੈ। ਥੋੜ੍ਹੀ ਦੇਰ ਬਾਅਦ ਫਿਰ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "telugu": "ఇప్పుడు కొంచెం ఇబ్బంది ఉంది. కాసేపు తర్వాత మళ్ళీ ప్రయత్నించు.",
        "kannada": "ಈಗ ಸ್ವಲ್ಪ ತೊಂದರೆ ಆಗುತ್ತಿದೆ. ಸ್ವಲ್ಪ ಹೊತ್ತಿನ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸು.",
    },
    "daily_cap": {
        "hindi": "आज की demo limit पूरी हो गई है। कल फिर आना, या video देख लो।",
        "english": "Today's demo limit is used up. Please come back tomorrow, or watch the video.",
    },
}


def say(key: str, lang: str = "hindi", voice: str = "male", **values: str) -> str:
    """One fixed phrase in the learner's language and the tutor's voice.

    `lang` is one of LANGUAGES, or "hinglish". Hinglish speakers get the
    Hindi phrase, which already keeps English words in English. A language
    with no phrase falls back to Hindi.
    """
    phrases = STRINGS[key]
    text = phrases.get(lang) or phrases["hindi"]
    if isinstance(text, tuple):
        text = text[1] if voice == "female" else text[0]
    return text.format(**values) if values else text
