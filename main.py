import spacy
import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import random
import sys
import requests
from datetime import datetime
from fuzzywuzzy import fuzz
import streamlit as st
import speech_recognition as sr

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


# Hugging Face API setup
HF_API_KEY = "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"
HF_CHATBOT_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HF_MODEL_URL1 = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

def ask_huggingface1(question):
    """
    Queries Hugging Face API (Mistral-7B) for command understanding.
    """
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(HF_MODEL_URL1, headers=headers, json={"inputs": question,  "parameters": {"return_full_text": False}})

    print(response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("fgregrgrger")
        print(result)
        return result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "None")
    return "None"

def ask_huggingface(question):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    data = {"inputs": question}
    response = requests.post(HF_CHATBOT_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return "Sorry, I couldn't understand the response format."
    else:
        return "Sorry, I couldn't fetch an answer right now."

# Speech function
def speak(text):
    print(f"Assistant: {text}")
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    return text  # Return the spoken text

# Command dictionary
command_actions = {
    "hello": lambda: speak("Hello! How can I assist you?"),
    "open notepad": lambda: (os.system("notepad"), speak("Opening Notepad...")),
    "open calculator": lambda: (os.system("calc"), speak("Opening Calculator...")),
    "open file explorer": lambda: (os.system("explorer"), speak("Opening File Explorer...")),
    "open task manager": lambda: (os.system("taskmgr"), speak("Opening Task Manager...")),
    "open control panel": lambda: (os.system("control"), speak("Opening Control Panel...")),
    "restart computer": lambda: (speak("Restarting your computer..."), os.system("shutdown /r /t 0")),
    "shutdown computer": lambda: (speak("Shutting down your computer..."), os.system("shutdown /s /t 0")),
    "play music": lambda: (os.system("start wmplayer"), speak("Playing music!")),
    "open google": lambda: (webbrowser.open("https://www.google.com"), speak("Opening Google...")),
    "open youtube": lambda: (webbrowser.open("https://www.youtube.com"), speak("Opening YouTube...")),
    "what time is it": lambda: speak(f"The time is {datetime.now().strftime('%H:%M:%S')}"),
    "what date is it": lambda: speak(f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"),
    "tell me a joke": lambda: speak(random.choice([
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "What do you call fake spaghetti? An impasta!",
        "Why don't skeletons fight each other? They don't have the guts!"
    ])),
    "flip a coin": lambda: speak(f"The coin landed on {random.choice(['Heads', 'Tails'])}."),
    "roll a dice": lambda: speak(f"You rolled a {random.randint(1,6)}."),
    "exit": lambda: (speak("Goodbye! Have a nice day."), sys.exit())
}


def find_best_match(command):
    command_tokens = set(token.text.lower() for token in nlp(command) if not token.is_stop and token.is_alpha)
    command_vector = nlp(command).vector  # Semantic similarity vector

    print(f"Command tokens: {command_tokens}")

    best_match = None
    best_score = 0

    for key in command_actions.keys():
        key_tokens = set(token.text.lower() for token in nlp(key) if not token.is_stop and token.is_alpha)
        key_vector = nlp(key).vector

        # Compute word overlap score
        match_score = len(command_tokens.intersection(key_tokens))

        # Compute fuzzy match score (handles typos, extra words)
        fuzzy_score = fuzz.ratio(command.lower(), key.lower())

        # Compute semantic similarity (meaning-based)
        semantic_score = nlp(command).similarity(nlp(key))

        # Weighted combination of scores
        total_score = (match_score * 3) + (fuzzy_score * 2) + (semantic_score * 100)

        print(f"Key: {key}, Tokens: {key_tokens}, Match Score: {match_score}, Fuzzy Score: {fuzzy_score}, Semantic Score: {semantic_score:.2f}, Total Score: {total_score:.2f}")

        if total_score > best_score:
            best_score = total_score
            best_match = key

    print(f"✅ Best Match: {best_match} (Score: {best_score})")
    return best_match if best_match else None

def has_negation(text, target_phrase):
    """Check if a specific command (target_phrase) is negated in the sentence."""
    doc = nlp(text)
    target_tokens = set(token.text.lower() for token in nlp(target_phrase) if not token.is_stop and token.is_alpha)

    for token in doc:
        if token.dep_ == "neg":
            # Check if negation is close to any of the target words
            for child in token.head.subtree:
                if child.text.lower() in target_tokens:
                    return True  # Negation applies to this phrase

    return False

def execute_command(command):
    """Processes user command and executes valid actions while respecting negation."""
    doc = nlp(command.lower())
    commands_to_execute = []
    spoken_responses = []

    for key in command_actions.keys():
        key_tokens = set(token.text.lower() for token in nlp(key) if not token.is_stop and token.is_alpha)

        if key_tokens.issubset(set(token.text.lower() for token in doc if token.is_alpha)):
            # Check if negation applies to this command
            if has_negation(command, key):
                print(f"❌ Skipping {key} due to negation.")
                continue  
            
            commands_to_execute.append(key)

    if commands_to_execute:
        for cmd in commands_to_execute:
            spoken_text = command_actions[cmd]()
            spoken_responses.append((cmd, spoken_text if isinstance(spoken_text, str) else spoken_text[1]))

            filtered_spoken_responses = [text if isinstance(text, str) else text[1] for text in spoken_responses]


        return f"✅ Executed: {', '.join(commands_to_execute)} ------------ \t Spoke🎤 : {', '.join(map(str, filtered_spoken_responses))}"



    hf_prompt = (
    f"Analyze the user's command: '{command}'. "
    f"Given the available commands: {', '.join(command_actions.keys())}, "
    f"identify the best matching command while considering negations (e.g., 'do not open YouTube' means YouTube should not be opened. Open google but do not open youtube should return open google). "
    f"Return ONLYYYYY the exact matching command (no explanation) or 'None' if no suitable match is found. do NOT repeat the query,just return the exact matching command (if any) "
)

    ai_response = ask_huggingface1(hf_prompt)
    print("THISSS")
    print(ai_response)
    print(ai_response.lower)
    if ai_response.strip().lower() != "none":
        print("erfgergergergerg")
        doc = nlp(ai_response.lower())
        commands_to_execute = []
    
        for key in command_actions.keys():
            key_tokens1 = set(token.text.lower() for token in nlp(key) if not token.is_stop and token.is_alpha)
    
            if key_tokens1.issubset(set(token.text.lower() for token in doc if token.is_alpha)):
                # Check if negation applies to this command
                if has_negation(ai_response, key):
                    print(f"❌ Skipping {key} due to negation.")
                    continue  # Skip this command
                
                commands_to_execute.append(key)
    
        if commands_to_execute:
            for cmd in commands_to_execute:
                spoken_text = command_actions[cmd]()
                spoken_responses.append(spoken_text)
                filtered_spoken_responses = [text for _, text in spoken_responses]
            return f"✅ Executed: {', '.join(commands_to_execute)}----------- Spoke🎤 : {', '.join(filtered_spoken_responses)}"


    else:
        ai_response1 = ask_huggingface(command)
        speak(ai_response1)
        return f"🤖  {ai_response1}"


# Streamlit UI Configuration
st.set_page_config(page_title="AI Voice Assistant", page_icon="🎙️", layout="wide")

# Custom Styles
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #1e1e2e, #2a2a40);
    }
    .main-container {
        background: rgba(255, 255, 255, 0.1);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .title {
        color: #f8f9fa;
        font-size: 3rem;
        font-weight: 600;
        text-align: center;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .subtitle {
        color: #b3b3b3;
        font-size: 1.2rem;
        text-align: center;
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff6b6b, #ffcc5c);
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 0.8rem 2rem;
        border-radius: 50px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(0,0,0,0.4);
        background: linear-gradient(45deg, #ffcc5c, #ff6b6b);
    }
    .status {
        font-size: 1.2rem;
        text-align: center;
        margin: 1rem 0;
        color: #ffffff;
        font-weight: 600;
    }
    .output-container {
        background-color: rgba(255, 255, 255, 0.15);
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1.5rem;
        color: #ffffff;
        text-align: center;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #808080;
        font-size: 0.9rem;
    }
    .sidebar-content {
        background: linear-gradient(135deg, #ff914d, #ffcc5c);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-weight: 600;
        font-size: 1.2rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .sidebar-instructions {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        color: #fff;
        text-align: left;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Menu
st.sidebar.markdown('<div class="sidebar-content">📌 Instructions</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-instructions">', unsafe_allow_html=True)
st.sidebar.write("✔ Click the 'Start Listening' button to begin.")
st.sidebar.write("✔ Speak clearly into your microphone.")
st.sidebar.write("✔ Wait for the assistant to process and respond.")
st.sidebar.write("✔ If there's an issue, check your internet connection.")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Main Content
st.markdown('<h1 style="color: #e0e0e0; text-align: center;">🎙️ AI Voice Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your intelligent voice-powered companion</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🎤 Start Listening", use_container_width=True):
        st.markdown('<div class="status">🎙️ Listening...</div>', unsafe_allow_html=True)
        
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio)
                
                st.markdown(f'<div class="output-container">🗣️ You said: <strong>{command}</strong></div>', unsafe_allow_html=True)
                response = execute_command(command)
                st.markdown(f'<div class="output-container">🤖 Assistant: <strong>{response}</strong></div>', unsafe_allow_html=True)
                
            except sr.UnknownValueError:
                st.warning("🤔 Sorry, I couldn't understand.")
            except sr.RequestError:
                st.error("⚠️ Could not request results. Check your internet connection.")

# Footer
st.markdown("""
    <div class="footer">
        <p>Powered by AI | Created with ❤️</p>
    </div>
""", unsafe_allow_html=True)
