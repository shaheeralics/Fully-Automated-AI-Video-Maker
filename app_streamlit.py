"""
Fully Automated AI Video Maker - Compact Version
Simple topic → video → upload workflow
"""

import streamlit as st
import os
import docx
import requests

# Page config
st.set_page_config(
    page_title="AI Video Maker",
    page_icon="🎬",
    layout="wide"
)

# Minimal futuristic styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    .stApp {
        background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2a2a6e 100%);
        color: #e0e0ff;
        font-family: 'Space Grotesk', sans-serif;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, rgba(0,255,255,0.2) 0%, rgba(128,0,255,0.2) 100%);
        border: 1px solid rgba(0,255,255,0.5);
        color: #ffffff;
        font-weight: 600;
    }
    .compact-input {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Simple title
st.markdown('<h1 class="main-title">AI Video Maker</h1>', unsafe_allow_html=True)

# Add space between title and content
st.markdown("<br>", unsafe_allow_html=True)

# API keys from Streamlit secrets
gemini_api_key = st.secrets["gemini_api"] if "gemini_api" in st.secrets else None
elevenlab_api_key = st.secrets["elevenlab_api"] if "elevenlab_api" in st.secrets else None

# ElevenLabs get voices function (must be defined before use)
def get_elevenlabs_voices(api_key):
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            voices_data = response.json()
            return voices_data.get('voices', [])
        else:
            st.error(f"Failed to load voices: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error loading voices: {str(e)}")
        return []

# HeyGen get avatars function (must be defined before use)
def get_heygen_avatars(api_key):
    url = "https://api.heygen.com/v2/avatars"
    headers = {"X-API-KEY": api_key}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            avatars_data = response.json()
            return avatars_data.get('data', {}).get('avatars', [])
        else:
            st.error(f"Failed to load avatars: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error loading avatars: {str(e)}")
        return []

# Load prompt.txt
def load_prompt():
    with open("assets/prompt.txt", encoding="utf-8") as f:
        return f.read()

# Load sample_scripts.docx
def load_sample_scripts():
    doc = docx.Document("assets/sample_scripts.docx")
    scripts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            scripts.append(text)
    return "\n".join(scripts)

# Gemini API call
def generate_script_gemini(topic, prompt, samples, api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": f"{prompt}\n\nSample Scripts:\n{samples}\n\nVideo Topic: {topic}"}]}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "[Error: Unexpected Gemini API response format]"
    else:
        return f"[Error: Gemini API returned {response.status_code}]"

# ElevenLabs API call
def generate_voice_elevenlabs(script, api_key, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": script,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"ElevenLabs API error: {response.status_code}")
        return None

# HeyGen API call (placeholder)
def generate_video_heygen(audio_bytes, api_key, avatar_id):
    # Placeholder for HeyGen API integration
    # This would upload audio and sync with avatar
    return "placeholder_video.mp4"

# YouTube upload (placeholder)
def upload_to_youtube(video_file, title, api_key):
    # Placeholder for YouTube API integration
    return "https://youtube.com/watch?v=placeholder"

# Single line: HeyGen API, Load Avatars, Avatar Dropdown, YouTube API, Load Voices, Voice Dropdown
col_a, col_b, col_c, col_d, col_e, col_f = st.columns([1.2, 0.8, 1.2, 1.2, 0.8, 1.2])

with col_a:
    heygen_api_key = st.text_input("HeyGen API Key", type="password", help="Required for avatar video generation")

with col_b:
    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
    if st.button("Load Avatars", help="Load available HeyGen avatars"):
        if heygen_api_key:
            with st.spinner("Loading avatars..."):
                avatars = get_heygen_avatars(heygen_api_key)
                if avatars:
                    st.session_state.available_avatars = avatars
                    st.session_state.avatars_loaded = True
                else:
                    st.session_state.avatar_error = True

with col_c:
    # Avatar dropdown or error (only shows if loaded successfully or error)
    if 'avatars_loaded' in st.session_state and st.session_state.avatars_loaded:
        avatar_options = [(f"{avatar['avatar_name']}", avatar['avatar_id']) for avatar in st.session_state.available_avatars]
        selected_avatar = st.selectbox(
            "Select Avatar", 
            avatar_options,
            format_func=lambda x: x[0],
            key="avatar_selector"
        )
        if selected_avatar:
            st.session_state.selected_avatar_id = selected_avatar[1]
    elif 'avatar_error' in st.session_state and st.session_state.avatar_error:
        st.markdown('<div style="margin-top: 35px;"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.8em; color:#ff6666; margin-bottom:0;">Failed to load avatars</p>', unsafe_allow_html=True)

with col_d:
    youtube_api_key = st.text_input("YouTube API Key", type="password", help="Required for uploading video")

with col_e:
    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
    if st.button("Load Voices", help="Load available ElevenLabs voices"):
        if elevenlab_api_key:
            with st.spinner("Loading voices..."):
                voices = get_elevenlabs_voices(elevenlab_api_key)
                if voices:
                    st.session_state.available_voices = voices
                    st.session_state.voices_loaded = True
                else:
                    st.session_state.voice_error = True
        else:
            st.session_state.voice_error = True

with col_f:
    # Voice dropdown or error (only shows if loaded successfully or error)
    if 'voices_loaded' in st.session_state and st.session_state.voices_loaded:
        voice_options = [(f"{voice['name']}", voice['voice_id']) for voice in st.session_state.available_voices]
        selected_voice = st.selectbox(
            "Select Voice", 
            voice_options,
            format_func=lambda x: x[0],
            key="voice_selector"
        )
        if selected_voice:
            st.session_state.selected_voice_id = selected_voice[1]
    elif 'voice_error' in st.session_state and st.session_state.voice_error:
        st.markdown('<div style="margin-top: 35px;"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.8em; color:#ff6666; margin-bottom:0;">Failed to load voices</p>', unsafe_allow_html=True)

# Second line: Topic input and Create Video button (centered with 15% padding)
col_left, col_center, col_right = st.columns([0.15, 0.7, 0.15])

with col_center:
    topic = st.text_input("Enter your video topic:", placeholder="e.g., AI in Pakistan", key="topic_input")
    
    if st.button("Create Video", disabled=not topic, key="create_video"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Generate Script
            status_text.text("Generating script...")
            progress_bar.progress(20)
            prompt = load_prompt()
            samples = load_sample_scripts()
            script = generate_script_gemini(topic, prompt, samples, gemini_api_key)
            st.session_state.generated_script = script
            
            # Step 2: Generate Voice
            status_text.text("Generating voice...")
            progress_bar.progress(40)
            voice_id = st.session_state.get('selected_voice_id', 'your_cloned_voice_id')
            audio_bytes = generate_voice_elevenlabs(script, elevenlab_api_key, voice_id)
            if audio_bytes:
                st.session_state.generated_audio = audio_bytes
                
                # Step 3: Generate Video
                status_text.text("Creating video with avatar...")
                progress_bar.progress(70)
                avatar_id = st.session_state.get('selected_avatar_id', 'your_avatar_id')
                video_file = generate_video_heygen(audio_bytes, heygen_api_key, avatar_id)
                st.session_state.generated_video = video_file
                
                progress_bar.progress(100)
                status_text.text("Video ready!")
                st.session_state.video_ready = True
                st.success("Video created successfully!")
            else:
                st.error("Failed to generate voice")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.caption("AI Video Maker - Powered by Gemini, ElevenLabs, HeyGen & YouTube APIs")
