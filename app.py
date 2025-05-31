import os
import json
import groq  # type: ignore
import streamlit as st  # type: ignore
import speech_recognition as sr

# Load JSON Data
def load_subjects():
    with open("subjects.json", "r") as file:
        data = json.load(file)
        if not isinstance(data, dict):  
            raise ValueError("Invalid JSON format! Expected a dictionary.")
        return data

courses = load_subjects()  

# Securely Load API Key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API Key not found! Set GROQ_API_KEY in your environment variables.")
    st.stop()

# Initialize Groq Client
client = groq.Client(api_key=api_key)

st.title("🎓 AI Tutor with Course Integration")

# Sidebar for Subject & Topic Selection
st.sidebar.title("📚 Subject & Topic Selection")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I’m your AI tutor. Select a subject from the sidebar to get started!"}
    ]
if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = None
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = None

# **1️⃣ Sidebar: Subject & Topic Selection**
subject = st.sidebar.selectbox("Select a subject:", ["Select"] + list(courses.keys()), key="subject")

if subject != "Select":
    topics = courses[subject]  
    topic = st.sidebar.selectbox("Select a topic:", ["Select"] + topics, key="topic")

    if topic != "Select":
        # Only update if there's a new selection
        if subject != st.session_state.selected_subject or topic != st.session_state.selected_topic:
            st.session_state.selected_subject = subject
            st.session_state.selected_topic = topic
            
            # Fetch explanation dynamically
            query = f"Explain {topic} in {subject}"
            with st.spinner("Fetching details..."):
                try:
                    response = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[{"role": "user", "content": query}]
                    )
                    explanation = response.choices[0].message.content
                except Exception as e:
                    explanation = f"An error occurred: {e}"

            # Store & Display Explanation
            st.session_state.messages.append({"role": "assistant", "content": f"📖 **{topic} - {subject}**\n\n{explanation}"})
            with st.chat_message("assistant"):
                st.write(f"📖 **{topic} - {subject}**\n\n{explanation}")

# **2️⃣ Display Chat History**
st.write("## 🗂️ Chat History")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# **3️⃣ User Query Input**
st.write("## 💬 Ask Your Questions")
user_input = st.chat_input(f"Ask me anything about {st.session_state.selected_topic or 'your topic'}...")

# Speech Recognition
recognizer = sr.Recognizer()

def record_audio():
    with sr.Microphone() as source:
        st.write("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not recognize the audio, please try again."
        except sr.RequestError:
            return "Speech Recognition service is unavailable."
        except Exception as e:
            return f"Error: {str(e)}"

# Speech-to-Text Button
if st.button("🎙️ Speak"):
    st.write("Recording...")
    user_input = record_audio()
    if user_input:
        st.success(f"Recognized Text: {user_input}")

# Process User Input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("Thinking..."):
        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=st.session_state.messages
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            response_text = f"An error occurred: {e}"

    # Store & display response
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    with st.chat_message("assistant"):
        st.write(response_text)
