"""Two-language string table for the public helper page (?lang=hi)."""

LANGS = ("en", "hi")

STRINGS = {
    "en": {
        "lang_name": "English",
        "other_lang_name": "हिन्दी",
        "emergency": "Medical emergency",
        "card_title": "LifeCard emergency card",
        "scanned_line": "You scanned this person's LifeCard. Here is what they chose to share.",
        "step_title": "What to do right now",
        "step_1": "Keep them still and check if they are breathing.",
        "step_2": "Call the ambulance on 112 and read out the details below.",
        "step_3": "Share your location so their family can reach you.",
        "call_ambulance": "Call ambulance 112",
        "call_ambulance_sub": "Free, 24x7 emergency number in India",
        "blood_group": "Blood group",
        "medical_alerts": "Medical alerts",
        "alerts_hidden": "Medical alerts are not shared on this card.",
        "about": "About this person",
        "age_sex": "Age / sex",
        "years": "years",
        "phone": "Their phone",
        "address": "Their address",
        "emergency_contact": "Emergency contact",
        "call": "Call",
        "call_now": "Call now",
        "hidden": "Not shared by the cardholder",
        "hidden_short": "Not shared",
        "location_title": "Help their family find you",
        "location_body": "Your location is sent once and only to this person's family. Nothing else is collected.",
        "share_location": "Share my location with their family",
        "sharing": "Sharing your location...",
        "shared": "Location shared with their family",
        "share_failed": "Could not get your location. You can still call 112.",
        "find_hospital": "Find nearest hospital",
        "doctor_title": "Are you a doctor or paramedic?",
        "doctor_body": "Full medical records - medication, history and notes - are only opened for verified doctors, and every access is logged for the cardholder.",
        "doctor_cta": "I'm a doctor",
        "consent_footer": "The cardholder decides what appears on this page. Hidden fields were switched off by them.",
        "preview_badge": "Preview - nothing is logged",
        "organ_donor": "Registered organ donor",
        "switch_lang": "हिन्दी में देखें",
        "scan_logged": "Scan logged",
        "scan_logged_body": "Their family has been alerted that the card was scanned.",
    },
    "hi": {
        "lang_name": "हिन्दी",
        "other_lang_name": "English",
        "emergency": "मेडिकल इमरजेंसी",
        "card_title": "लाइफकार्ड इमरजेंसी कार्ड",
        "scanned_line": "आपने इस व्यक्ति का लाइफकार्ड स्कैन किया है। उन्होंने यह जानकारी साझा करना चुना है।",
        "step_title": "अभी क्या करें",
        "step_1": "उन्हें हिलाएँ नहीं और देखें कि वे साँस ले रहे हैं या नहीं।",
        "step_2": "112 पर एम्बुलेंस बुलाएँ और नीचे दी गई जानकारी बताएँ।",
        "step_3": "अपनी लोकेशन साझा करें ताकि उनका परिवार आप तक पहुँच सके।",
        "call_ambulance": "एम्बुलेंस 112 पर कॉल करें",
        "call_ambulance_sub": "भारत में निःशुल्क, चौबीसों घंटे आपातकालीन नंबर",
        "blood_group": "ब्लड ग्रुप",
        "medical_alerts": "मेडिकल अलर्ट",
        "alerts_hidden": "इस कार्ड पर मेडिकल अलर्ट साझा नहीं किए गए हैं।",
        "about": "इस व्यक्ति के बारे में",
        "age_sex": "उम्र / लिंग",
        "years": "वर्ष",
        "phone": "उनका फ़ोन नंबर",
        "address": "उनका पता",
        "emergency_contact": "आपातकालीन संपर्क",
        "call": "कॉल",
        "call_now": "अभी कॉल करें",
        "hidden": "कार्डधारक ने साझा नहीं किया",
        "hidden_short": "साझा नहीं किया",
        "location_title": "उनके परिवार को आप तक पहुँचने में मदद करें",
        "location_body": "आपकी लोकेशन केवल एक बार, केवल इस व्यक्ति के परिवार को भेजी जाती है। और कुछ नहीं लिया जाता।",
        "share_location": "अपनी लोकेशन उनके परिवार से साझा करें",
        "sharing": "आपकी लोकेशन भेजी जा रही है...",
        "shared": "लोकेशन उनके परिवार के साथ साझा कर दी गई",
        "share_failed": "आपकी लोकेशन नहीं मिल सकी। आप फिर भी 112 पर कॉल कर सकते हैं।",
        "find_hospital": "नज़दीकी अस्पताल खोजें",
        "doctor_title": "क्या आप डॉक्टर या पैरामेडिक हैं?",
        "doctor_body": "पूरा मेडिकल रिकॉर्ड - दवाएँ, इतिहास और नोट्स - केवल सत्यापित डॉक्टरों के लिए खोला जाता है, और हर एक्सेस कार्डधारक के लिए दर्ज किया जाता है।",
        "doctor_cta": "मैं डॉक्टर हूँ",
        "consent_footer": "इस पेज पर क्या दिखेगा, यह कार्डधारक तय करते हैं। छिपाई गई जानकारी उन्होंने बंद कर रखी है।",
        "preview_badge": "प्रीव्यू - कुछ भी दर्ज नहीं हो रहा",
        "organ_donor": "रजिस्टर्ड अंगदाता",
        "switch_lang": "View in English",
        "scan_logged": "स्कैन दर्ज हुआ",
        "scan_logged_body": "उनके परिवार को सूचित कर दिया गया है कि कार्ड स्कैन किया गया है।",
    },
}


def normalise(lang):
    return lang if lang in LANGS else "en"


def translator(lang):
    lang = normalise(lang)
    table = STRINGS[lang]
    fallback = STRINGS["en"]

    def t(key):
        return table.get(key, fallback.get(key, key))

    return t
