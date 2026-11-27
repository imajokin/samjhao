// The words on the screens, in the five app languages.
//
// The learner can change the language at the top of the first screen.
// English is shown as a second, smaller line next to the other languages,
// because learners study from English textbooks.
//
// The Punjabi, Telugu and Kannada lines still need a check by a native speaker.

const LANGUAGE_NAMES = {
  hindi: "हिन्दी",
  english: "English",
  punjabi: "ਪੰਜਾਬੀ",
  telugu: "తెలుగు",
  kannada: "ಕನ್ನಡ",
};

const I18N = {
  english: {
    pitch: "Did you really understand it, or just memorise it? Explain it to Samjhao and you will know.",
    plan: "At most 3 short questions, to see how far your understanding goes. Then the full explanation with a diagram.",
    voice: "Voice",
    choose_class: "Choose your class",
    prompt: "Tap the mic, say the topic and start explaining.",
    tap_to_speak: "Tap the mic and speak",
    listening: "Listening… tap again to send",
    pausing: "Still thinking? Keep talking, or it sends in {n}s",
    pick_class: "Choose your class first",
    cancel: "Cancel",
    type_instead: "Type instead",
    type_topic: "Type the topic and your explanation",
    start: "Start",
    examples: "Not sure? Try one of these:",
    step1: "You explain.",
    step2: "Samjhao listens and asks at most 3 short questions.",
    step3: "Stuck? You get a hint, not the answer.",
    step4: "At the end, the full explanation with a diagram.",
    privacy: "No login. Nothing you say is saved.",
    you_said: "You said",
    type_answer: "Type your answer",
    send: "Send",
    points_title: "What you explained",
    legend_green: "You explained it on your own",
    legend_amber: "Needed a hint, or Samjhao explained it",
    legend_skipped: "We did not get to this one",
    diagram_note: "Drawn by Samjhao; it may not be exact.",
    language: "Language",
  },
  hindi: {
    pitch: "समझ आया है, या सिर्फ़ याद है? Samjhao को समझाकर देखो, तुरंत पता चल जाएगा।",
    plan: "ज़्यादा से ज़्यादा 3 छोटे सवाल, यह देखने के लिए कि तुम्हें कहाँ तक समझ आया। फिर पूरा explanation, diagram के साथ।",
    voice: "आवाज़",
    choose_class: "अपनी class चुनो",
    prompt: "Mic दबाओ, topic बोलो और समझाना शुरू करो।",
    tap_to_speak: "Mic दबाओ और बोलो",
    listening: "सुन रहा हूँ… भेजने के लिए फिर दबाओ",
    pausing: "सोच रहे हो? बोलते रहो। चुप रहे तो {n} सेकंड में भेज दूँगा",
    pick_class: "पहले अपनी class चुनो",
    cancel: "रद्द करो",
    type_instead: "Type करके बताओ",
    type_topic: "Topic और अपना explanation type करो",
    start: "शुरू करो",
    examples: "पक्का नहीं? इनमें से एक चुनो:",
    step1: "तुम समझाओ।",
    step2: "Samjhao सुनता है और ज़्यादा से ज़्यादा 3 छोटे सवाल पूछता है।",
    step3: "अटक गए? Hint मिलेगा, जवाब नहीं।",
    step4: "आख़िर में पूरा explanation, diagram के साथ।",
    privacy: "Login नहीं। तुम्हारी कोई बात save नहीं होती।",
    you_said: "तुमने कहा",
    type_answer: "अपना जवाब type करो",
    send: "भेजो",
    points_title: "तुमने क्या समझाया",
    legend_green: "तुमने खुद समझाया",
    legend_amber: "Hint लगा, या Samjhao ने समझाया",
    legend_skipped: "इस पर बात नहीं हुई",
    diagram_note: "Samjhao ने यह diagram खुद बनाया है, इसमें छोटी गलती हो सकती है।",
    language: "भाषा",
  },
  punjabi: {
    pitch: "ਸਮਝ ਆਇਆ ਹੈ, ਜਾਂ ਸਿਰਫ਼ ਯਾਦ ਹੈ? Samjhao ਨੂੰ ਸਮਝਾ ਕੇ ਵੇਖੋ, ਤੁਰੰਤ ਪਤਾ ਲੱਗ ਜਾਵੇਗਾ।",
    plan: "ਵੱਧ ਤੋਂ ਵੱਧ 3 ਛੋਟੇ ਸਵਾਲ, ਇਹ ਵੇਖਣ ਲਈ ਕਿ ਤੁਹਾਨੂੰ ਕਿੱਥੋਂ ਤੱਕ ਸਮਝ ਆਇਆ। ਫਿਰ ਪੂਰਾ explanation, diagram ਦੇ ਨਾਲ।",
    voice: "ਆਵਾਜ਼",
    choose_class: "ਆਪਣੀ class ਚੁਣੋ",
    prompt: "Mic ਦਬਾਓ, topic ਬੋਲੋ ਅਤੇ ਸਮਝਾਉਣਾ ਸ਼ੁਰੂ ਕਰੋ।",
    tap_to_speak: "Mic ਦਬਾਓ ਅਤੇ ਬੋਲੋ",
    listening: "ਸੁਣ ਰਿਹਾ ਹਾਂ… ਭੇਜਣ ਲਈ ਫਿਰ ਦਬਾਓ",
    pausing: "ਸੋਚ ਰਹੇ ਹੋ? ਬੋਲਦੇ ਰਹੋ। ਚੁੱਪ ਰਹੇ ਤਾਂ {n} ਸਕਿੰਟ ਵਿੱਚ ਭੇਜ ਦਿਆਂਗਾ",
    pick_class: "ਪਹਿਲਾਂ ਆਪਣੀ class ਚੁਣੋ",
    cancel: "ਰੱਦ ਕਰੋ",
    type_instead: "Type ਕਰਕੇ ਦੱਸੋ",
    type_topic: "Topic ਅਤੇ ਆਪਣਾ explanation type ਕਰੋ",
    start: "ਸ਼ੁਰੂ ਕਰੋ",
    examples: "ਪੱਕਾ ਨਹੀਂ? ਇਹਨਾਂ ਵਿੱਚੋਂ ਇੱਕ ਚੁਣੋ:",
    step1: "ਤੁਸੀਂ ਸਮਝਾਓ।",
    step2: "Samjhao ਸੁਣਦਾ ਹੈ ਅਤੇ ਵੱਧ ਤੋਂ ਵੱਧ 3 ਛੋਟੇ ਸਵਾਲ ਪੁੱਛਦਾ ਹੈ।",
    step3: "ਅਟਕ ਗਏ? Hint ਮਿਲੇਗਾ, ਜਵਾਬ ਨਹੀਂ।",
    step4: "ਅਖੀਰ ਵਿੱਚ ਪੂਰਾ explanation, diagram ਦੇ ਨਾਲ।",
    privacy: "Login ਨਹੀਂ। ਤੁਹਾਡੀ ਕੋਈ ਗੱਲ save ਨਹੀਂ ਹੁੰਦੀ।",
    you_said: "ਤੁਸੀਂ ਕਿਹਾ",
    type_answer: "ਆਪਣਾ ਜਵਾਬ type ਕਰੋ",
    send: "ਭੇਜੋ",
    points_title: "ਤੁਸੀਂ ਕੀ ਸਮਝਾਇਆ",
    legend_green: "ਤੁਸੀਂ ਆਪ ਸਮਝਾਇਆ",
    legend_amber: "Hint ਲੱਗਾ, ਜਾਂ Samjhao ਨੇ ਸਮਝਾਇਆ",
    legend_skipped: "ਇਸ ਬਾਰੇ ਗੱਲ ਨਹੀਂ ਹੋਈ",
    diagram_note: "Samjhao ਨੇ ਇਹ diagram ਆਪ ਬਣਾਇਆ ਹੈ, ਇਸ ਵਿੱਚ ਛੋਟੀ ਗਲਤੀ ਹੋ ਸਕਦੀ ਹੈ।",
    language: "ਭਾਸ਼ਾ",
  },
  telugu: {
    pitch: "నిజంగా అర్థమైందా, లేక గుర్తుపెట్టుకున్నావా? Samjhao కి వివరించి చూడు, వెంటనే తెలిసిపోతుంది.",
    plan: "గరిష్ఠంగా 3 చిన్న ప్రశ్నలు, నీకు ఎంతవరకు అర్థమైందో చూడటానికి. తర్వాత పూర్తి explanation, diagram తో.",
    voice: "గొంతు",
    choose_class: "నీ class ఎంచుకో",
    prompt: "Mic నొక్కి, topic చెప్పి, వివరించడం మొదలుపెట్టు.",
    tap_to_speak: "Mic నొక్కి మాట్లాడు",
    listening: "వింటున్నాను… పంపడానికి మళ్ళీ నొక్కు",
    pausing: "ఆలోచిస్తున్నావా? మాట్లాడుతూ ఉండు. మౌనంగా ఉంటే {n} సెకన్లలో పంపేస్తాను",
    pick_class: "ముందు నీ class ఎంచుకో",
    cancel: "రద్దు చేయి",
    type_instead: "Type చేసి చెప్పు",
    type_topic: "Topic, నీ explanation type చేయి",
    start: "మొదలుపెట్టు",
    examples: "ఏది చెప్పాలో తెలియదా? వీటిలో ఒకటి ఎంచుకో:",
    step1: "నువ్వు వివరించు.",
    step2: "Samjhao వింటుంది, గరిష్ఠంగా 3 చిన్న ప్రశ్నలు అడుగుతుంది.",
    step3: "ఆగిపోయావా? Hint వస్తుంది, జవాబు కాదు.",
    step4: "చివరలో పూర్తి explanation, diagram తో.",
    privacy: "Login లేదు. నువ్వు చెప్పింది ఏదీ save కాదు.",
    you_said: "నువ్వు చెప్పింది",
    type_answer: "నీ జవాబు type చేయి",
    send: "పంపు",
    points_title: "నువ్వు ఏం వివరించావు",
    legend_green: "నువ్వే వివరించావు",
    legend_amber: "Hint అవసరమైంది, లేదా Samjhao వివరించింది",
    legend_skipped: "దీని గురించి మాట్లాడలేదు",
    diagram_note: "ఈ diagram ని Samjhao గీసింది, చిన్న తప్పులు ఉండవచ్చు.",
    language: "భాష",
  },
  kannada: {
    pitch: "ನಿಜವಾಗಿ ಅರ್ಥವಾಗಿದೆಯಾ, ಅಥವಾ ಬರೀ ನೆನಪಿದೆಯಾ? Samjhao ಗೆ ವಿವರಿಸಿ ನೋಡು, ತಕ್ಷಣ ಗೊತ್ತಾಗುತ್ತದೆ.",
    plan: "ಗರಿಷ್ಠ 3 ಚಿಕ್ಕ ಪ್ರಶ್ನೆಗಳು, ನಿನಗೆ ಎಷ್ಟರವರೆಗೆ ಅರ್ಥವಾಗಿದೆ ಎಂದು ನೋಡಲು. ನಂತರ ಪೂರ್ತಿ explanation, diagram ಜೊತೆ.",
    voice: "ಧ್ವನಿ",
    choose_class: "ನಿನ್ನ class ಆಯ್ಕೆ ಮಾಡು",
    prompt: "Mic ಒತ್ತಿ, topic ಹೇಳಿ, ವಿವರಿಸಲು ಶುರು ಮಾಡು.",
    tap_to_speak: "Mic ಒತ್ತಿ ಮಾತಾಡು",
    listening: "ಕೇಳುತ್ತಿದ್ದೇನೆ… ಕಳುಹಿಸಲು ಮತ್ತೆ ಒತ್ತು",
    pausing: "ಯೋಚಿಸುತ್ತಿದ್ದೀಯಾ? ಮಾತಾಡುತ್ತಿರು. ಸುಮ್ಮನಿದ್ದರೆ {n} ಸೆಕೆಂಡಿನಲ್ಲಿ ಕಳುಹಿಸುತ್ತೇನೆ",
    pick_class: "ಮೊದಲು ನಿನ್ನ class ಆಯ್ಕೆ ಮಾಡು",
    cancel: "ರದ್ದು ಮಾಡು",
    type_instead: "Type ಮಾಡಿ ಹೇಳು",
    type_topic: "Topic ಮತ್ತು ನಿನ್ನ explanation type ಮಾಡು",
    start: "ಶುರು ಮಾಡು",
    examples: "ಯಾವುದು ಎಂದು ಗೊತ್ತಿಲ್ಲವಾ? ಇವುಗಳಲ್ಲಿ ಒಂದನ್ನು ಆಯ್ಕೆ ಮಾಡು:",
    step1: "ನೀನು ವಿವರಿಸು.",
    step2: "Samjhao ಕೇಳುತ್ತದೆ, ಗರಿಷ್ಠ 3 ಚಿಕ್ಕ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತದೆ.",
    step3: "ಸಿಕ್ಕಿಕೊಂಡೆಯಾ? Hint ಸಿಗುತ್ತದೆ, ಉತ್ತರ ಅಲ್ಲ.",
    step4: "ಕೊನೆಯಲ್ಲಿ ಪೂರ್ತಿ explanation, diagram ಜೊತೆ.",
    privacy: "Login ಇಲ್ಲ. ನೀನು ಹೇಳಿದ್ದು ಯಾವುದೂ save ಆಗುವುದಿಲ್ಲ.",
    you_said: "ನೀನು ಹೇಳಿದ್ದು",
    type_answer: "ನಿನ್ನ ಉತ್ತರ type ಮಾಡು",
    send: "ಕಳುಹಿಸು",
    points_title: "ನೀನು ಏನು ವಿವರಿಸಿದೆ",
    legend_green: "ನೀನೇ ವಿವರಿಸಿದೆ",
    legend_amber: "Hint ಬೇಕಾಯಿತು, ಅಥವಾ Samjhao ವಿವರಿಸಿತು",
    legend_skipped: "ಇದರ ಬಗ್ಗೆ ಮಾತಾಡಲಿಲ್ಲ",
    diagram_note: "ಈ diagram ಅನ್ನು Samjhao ಬಿಡಿಸಿದೆ, ಚಿಕ್ಕ ತಪ್ಪುಗಳು ಇರಬಹುದು.",
    language: "ಭಾಷೆ",
  },
};

const Lang = {
  // The language chosen for the app. Hindi until the learner picks another.
  current: "hindi",
  // True once the learner has picked a language themselves.
  chosen: false,

  load() {
    try {
      const saved = localStorage.getItem("samjhao-language");
      if (saved && I18N[saved]) {
        this.current = saved;
        this.chosen = true;
      }
    } catch (error) {
      // Private windows may refuse storage. The app works without it.
    }
  },

  set(language) {
    if (!I18N[language]) return;
    this.current = language;
    this.chosen = true;
    try {
      localStorage.setItem("samjhao-language", language);
    } catch (error) {
      // Nothing to do: the choice simply lasts for this visit.
    }
  },

  // The words for `key` in the app language.
  t(key) {
    return (I18N[this.current] || {})[key] || I18N.hindi[key] || key;
  },

  // The same, followed by the English words (unless the app is in English).
  both(key) {
    if (this.current === "english") return I18N.english[key];
    return this.t(key) + " · " + I18N.english[key];
  },

  // Puts the words onto every element that asks for them:
  //   data-t="key"   the app language only
  //   data-tb="key"  the app language, then English
  // Elements with class "en2" are the smaller English lines; they are
  // hidden when the app itself is in English.
  apply() {
    document.documentElement.lang = { hindi: "hi", english: "en", punjabi: "pa", telugu: "te", kannada: "kn" }[this.current];
    for (const element of document.querySelectorAll("[data-t]")) {
      element.textContent = this.t(element.dataset.t);
    }
    for (const element of document.querySelectorAll("[data-tb]")) {
      element.textContent = this.both(element.dataset.tb);
    }
    for (const element of document.querySelectorAll(".en2")) {
      element.hidden = this.current === "english";
    }
  },
};
