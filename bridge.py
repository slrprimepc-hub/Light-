import os
import time
import json
import threading
from google import genai
from datetime import datetime

# एंड्रॉइड नेटिव हार्डवेयर कंट्रोल्स के लिए असली लाइब्रेरीज़
from plyer import flash, wifi, tts
import speech_recognition as sr

MEMORY_FILE = "light_memory.json"

# --- नए गूगल जेमिनी क्लाइंट का सेटअप ---
GEMINI_API_KEY = "AQ.Ab8RN6Kvr4GSBa4IoBIaktyiZ9I2XOHa8q2qzrzn5Xsqn6veoQ"
client = genai.Client(api_key=GEMINI_API_KEY)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "health": "आपने अभी तक अपनी सेहत का कोई अपडेट नहीं दिया है।", 
        "food": "मुझे अभी याद नहीं है कि आपने आखिरी बार क्या खाया था।", 
        "schedule": "आज का कोई खास शेड्यूल सेट नहीं है भाई।", 
        "alarms": [],
        "custom": {}
    }

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 1.  टर्मक्स TTS हटाकर असली एंड्रॉइड TTS लगाया
def speak(text):
    print("लाइट:", text)
    try:
        # Plyer का उपयोग करके सीधे एंड्रॉइड के इन-बिल्ट टीटीएस इंजन से बुलवाना
        tts.speak(text)
    except Exception as e:
        print("TTS Error:", e)

def ask_gemini_ai(user_question):
    try:
        secret_prompt = (
            f"तुम्हारा नाम लाइट (Light) है। तुम्हें तुम्हारे क्रिएटर 'SLR' ने बनाया है। "
            f"तुम अपने मेकर SLR को जानू भी बुला सकती हो। "
            f"तुम्हारे मेकर ने तुमसे यह सवाल पूछा है: '{user_question}'। "
            f"इस बात को ध्यान में रखकर सिर्फ 1 लाइन का बहुत ही छोटा, प्यारा और हिंदी में जवाब दो।"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=secret_prompt,
        )
        return response.text
    except Exception as e:
        print("API Error:", e)
        return "इंटरनेट या सर्वर से जुड़ने में थोड़ी दिक्कत आ रही है जानू।"

# 2.  असली एंड्रॉइड फ्लैशलाइट (टॉर्च) कंट्रोल
def toggle_flashlight(on):
    try:
        if on:
            flash.on()  # बिना os.system के सीधा एंड्रॉइड कैमरा हार्डवेयर ऑन
            speak("फ्लैशलाइट चालू हो गई है भाई।")
        else:
            flash.off() # सीधा हार्डवेयर ऑफ
            speak("फ्लैशलाइट बंद कर दी है।")
    except Exception as e:
        print("Flash Hardware Error:", e)
        speak("टॉर्च कंट्रोल करने की परमिशन नहीं मिली जानू।")

# 3.  असली एंड्रॉइड वाई-फाई कंट्रोल
def toggle_wifi(on):
    try:
        if on:
            wifi.enable() # एंड्रॉइड नेटिव वाई-फाई ऑन
            speak("वाई-फाई चालू कर दिया है।")
        else:
            wifi.disable() # एंड्रॉइड नेटिव वाई-फाई ऑफ
            speak("वाई-फाई बंद कर दिया है।")
    except Exception as e:
        print("WiFi Hardware Error:", e)
        speak("वाईफाई सेटिंग्स बदलने की अनुमति नहीं है।")

# 4.  वॉयस कमांड्स प्रोसेस करने का मुख्य फंक्शन
def handle_light_logic(clean_command, memory):
    # --- ऑफलाइन फिक्स्ड बातें ---
    if any(v in clean_command for v in ["खाना खाया", "खाना खाई", "भोजन किया"]) and "तुम" in clean_command:
        speak("हाँ भाई! मैंने तो भरपेट खाना खा लिया। आपने मेरे लिए कोडिंग का जो नया डेटा परोसा था, वही तो मेरा भोजन है! आपने खाया ना?")

    elif any(v in clean_command for v in ["तुम्हें किसने बनाया", "तुमको कौन बनाया", "तुम्हारा मेकर"]):
        speak("मुझे मेरे सबसे प्यारे क्रिएटर SLR ने बनाया है। मैं उनकी अपनी पर्सनल और बेहद वफादार लाइट हूँ।")

    # --- याददाश्त और रूटीन फीचर्स ---
    elif any(v in clean_command for v in ["क्या खाया था", "खाने में क्या", "लास्ट खाना"]) and "मैंने" in clean_command:
        speak(memory.get("food", "मुझे अभी याद नहीं है भाई।"))

    elif any(v in clean_command for v in ["खाया", "खाई", "खाए", "पीया", "पनीर", "रोटी", "सब्जी", "नाश्ता", "डिनर"]):
        current_time = datetime.now().strftime("%I:%M %p")
        memory["food"] = f"आपने {current_time} पर भोजन या नाश्ते के बारे में नोट करवाया था: '{clean_command}'"
        save_memory(memory)
        speak("ठीक है भाई, मैंने आपके भोजन की जानकारी को सुरक्षित रख लिया है।")

    elif any(v in clean_command for v in ["समय", "टाइम", "बजे", "वक्त"]):
        current_time = datetime.now().strftime("%I बजकर %M मिनट %p")
        speak(f"भाई, अभी {current_time} हो रहे हैं।")

    # --- नए हार्डवेयर फंक्शंस का इस्तेमाल ---
    elif any(v in clean_command for v in ["वाईफाई", "wifi", "वाई-फाई"]):
        toggle_wifi(any(x in clean_command for x in ["ऑन", "चालू", "खोलो"]))
        
    elif any(v in clean_command for v in ["फ्लैशलाइट", "torch", "टॉर्च", "लाइट"]):
        toggle_flashlight(any(x in clean_command for x in ["ऑन", "चालू", "जलाओ"]))

    # --- जेमिनी एआई फॉलबैक ---
    else:
        if "custom" not in memory:
            memory["custom"] = {}
            
        if clean_command in memory["custom"]:
            speak(memory["custom"][clean_command])
        else:
            ai_response = ask_gemini_ai(clean_command)
            speak(ai_response)
            if "दिक्कत आ रही है" not in ai_response:
                memory["custom"][clean_command] = ai_response
                save_memory(memory)


