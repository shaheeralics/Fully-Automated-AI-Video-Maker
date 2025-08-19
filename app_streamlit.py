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
    page_title="Idea to Video",
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
st.markdown('<h1 class="main-title">Idea to Video</h1>', unsafe_allow_html=True)

# Add space between title and content
st.markdown('<div style="margin-top: 70px;"></div>', unsafe_allow_html=True)

# API keys from Streamlit secrets
gemini_api_key = st.secrets["gemini_api"] if "gemini_api" in st.secrets else None
elevenlab_api_key = st.secrets["elevenlab_api"] if "elevenlab_api" in st.secrets else None
heygen_api_key = st.secrets["heygen_api"] if "heygen_api" in st.secrets else None

# YouTube API credentials from Streamlit secrets
youtube_credentials = {
    "client_id": st.secrets.get("youtube_client_id"),
    "project_id": st.secrets.get("youtube_project_id"),
    "auth_uri": st.secrets.get("youtube_auth_uri"),
    "token_uri": st.secrets.get("youtube_token_uri"),
    "auth_provider_x509_cert_url": st.secrets.get("youtube_auth_provider_x509_cert_url"),
    "client_secret": st.secrets.get("youtube_client_secret"),
    "redirect_uris": [st.secrets.get("youtube_redirect_uris")] if st.secrets.get("youtube_redirect_uris") else [],
    "javascript_origins": [st.secrets.get("youtube_javascript_origins")] if st.secrets.get("youtube_javascript_origins") else []
}

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
    # Updated Gemini API endpoint and model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt}\n\nSample Scripts:\n{samples}\n\nVideo Topic: {topic}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError) as e:
                return f"[Error: Unexpected Gemini API response format - {str(e)}]"
        else:
            # More detailed error information
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = f" - {error_response.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_detail = f" - Response: {response.text[:200]}"
            
            return f"[Error: Gemini API returned {response.status_code}{error_detail}]"
            
    except requests.exceptions.RequestException as e:
        return f"[Error: Network error - {str(e)}]"
    except Exception as e:
        return f"[Error: Unexpected error - {str(e)}]"

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

# YouTube upload function using credentials from secrets
def upload_to_youtube(video_file, title, credentials_dict):
    """
    Upload video to YouTube using credentials from Streamlit secrets
    Args:
        video_file: Path to the video file
        title: Video title
        credentials_dict: Dictionary containing YouTube API credentials
    """
    try:
        # Import required libraries for YouTube upload
        # from google.oauth2.credentials import Credentials
        # from googleapiclient.discovery import build
        # from googleapiclient.http import MediaFileUpload
        
        # Create credentials object from secrets
        # client_config = {
        #     "web": {
        #         "client_id": credentials_dict["client_id"],
        #         "client_secret": credentials_dict["client_secret"],
        #         "auth_uri": credentials_dict["auth_uri"],
        #         "token_uri": credentials_dict["token_uri"],
        #         "redirect_uris": credentials_dict["redirect_uris"]
        #     }
        # }
        
        # TODO: Implement actual YouTube upload logic here
        # This would involve OAuth2 flow and video upload
        
        # Placeholder return for now
        return "https://youtube.com/watch?v=placeholder"
        
    except Exception as e:
        st.error(f"YouTube upload error: {str(e)}")
        return None

# Single line: Load Avatars and Voices button, Select Avatar dropdown, Select Voice dropdown (conditional layout)
voices_loaded = 'voices_loaded' in st.session_state and st.session_state.voices_loaded
avatars_loaded = 'avatars_loaded' in st.session_state and st.session_state.avatars_loaded

if not voices_loaded or not avatars_loaded:
    # Center the button when not loaded
    col_left, col_center, col_right = st.columns([0.4, 0.2, 0.4])
    with col_center:
        if st.button("Load Avatars and Voices", key="load_all"):
            if heygen_api_key and elevenlab_api_key:
                with st.spinner("Loading avatars and voices..."):
                    # Load avatars
                    avatars = get_heygen_avatars(heygen_api_key)
                    if avatars:
                        st.session_state.available_avatars = avatars
                        st.session_state.avatars_loaded = True
                    
                    # Load voices
                    voices = get_elevenlabs_voices(elevenlab_api_key)
                    if voices:
                        st.session_state.available_voices = voices
                        st.session_state.voices_loaded = True
                    
                    # Force refresh to show new layout immediately
                    st.rerun()
else:
    # Normal layout when loaded
    col_left, col_center, col_right = st.columns([0.25, 0.5, 0.25])
    
    with col_center:
        # Three columns within center: button, avatar dropdown, voice dropdown
        btn_col, avatar_col, voice_col = st.columns([1, 1, 1])
        
        with btn_col:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            if st.button("Load Avatars and Voices", key="load_all_loaded"):
                if heygen_api_key and elevenlab_api_key:
                    with st.spinner("Loading avatars and voices..."):
                        # Load avatars
                        avatars = get_heygen_avatars(heygen_api_key)
                        if avatars:
                            st.session_state.available_avatars = avatars
                            st.session_state.avatars_loaded = True
                        
                        # Load voices
                        voices = get_elevenlabs_voices(elevenlab_api_key)
                        if voices:
                            st.session_state.available_voices = voices
                            st.session_state.voices_loaded = True
                        
                        # Force refresh to update dropdowns immediately
                        st.rerun()
        
        with avatar_col:
            # Avatar dropdown (shows only if loaded successfully)
            if avatars_loaded:
                avatar_options = [(f"{avatar['avatar_name']}", avatar['avatar_id']) for avatar in st.session_state.available_avatars]
                selected_avatar = st.selectbox(
                    "Select Avatar", 
                    avatar_options,
                    format_func=lambda x: x[0],
                    key="avatar_selector"
                )
                if selected_avatar:
                    st.session_state.selected_avatar_id = selected_avatar[1]
        
        with voice_col:
            # Voice dropdown (shows only if loaded successfully)
            if voices_loaded:
                voice_options = [(f"{voice['name']}", voice['voice_id']) for voice in st.session_state.available_voices]
                selected_voice = st.selectbox(
                    "Select Voice", 
                    voice_options,
                    format_func=lambda x: x[0],
                    key="voice_selector"
                )
                if selected_voice:
                    st.session_state.selected_voice_id = selected_voice[1]

# Second line: Topic input and testing buttons (conditional styling)
st.markdown('<div style="margin-top: 80px;"></div>', unsafe_allow_html=True)  # Add 80px padding from first line

# Check if voices and avatars are loaded for conditional styling
content_enabled = voices_loaded and avatars_loaded

col_left, col_center, col_right = st.columns([0.22, 0.7, 0.08])

with col_center:
    # Create columns: topic field, generate script button, generate voice button, create video (disabled)
    topic_col, script_btn_col, voice_btn_col, video_btn_col = st.columns([0.4, 0.2, 0.2, 0.2])
    
    with topic_col:
        topic = st.text_input(
            "Enter your video topic:", 
            placeholder="e.g., AI in Pakistan", 
            key="topic_input",
            disabled=not content_enabled
        )
        st.session_state.topic_value = topic if content_enabled else ""  # Store topic value for button state
    
    with script_btn_col:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        generate_script_clicked = st.button(
            "Generate Script", 
            disabled=not content_enabled or not st.session_state.get('topic_value', ''), 
            key="generate_script"
        )
    
    with voice_btn_col:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        generate_voice_clicked = st.button(
            "Generate Voice", 
            disabled=not content_enabled or not st.session_state.get('generated_script', ''), 
            key="generate_voice"
        )
    
    with video_btn_col:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        create_video_clicked = st.button(
            "Create Video", 
            disabled=True,  # Disabled for testing
            key="create_video"
        )
    
    # Handle Generate Script button click
    if generate_script_clicked and topic:
        try:
            prompt = load_prompt()
            samples = load_sample_scripts()
            script = generate_script_gemini(topic, prompt, samples, gemini_api_key)
            st.session_state.generated_script = script
            
            # Display generated script
            with st.expander("Generated Script", expanded=True):
                st.text_area("Script Content:", value=script, height=150, key="script_display")
                
        except Exception as e:
            st.error(f"Script generation error: {str(e)}")
    
    # Handle Generate Voice button click
    if generate_voice_clicked and st.session_state.get('generated_script'):
        try:
            voice_id = st.session_state.get('selected_voice_id', 'your_cloned_voice_id')
            script = st.session_state.generated_script
            audio_bytes = generate_voice_elevenlabs(script, elevenlab_api_key, voice_id)
            
            if audio_bytes:
                st.session_state.generated_audio = audio_bytes
                
                # Display audio player
                st.audio(audio_bytes, format="audio/mp3")
                
            else:
                st.error("Failed to generate voice")
                
        except Exception as e:
            st.error(f"Voice generation error: {str(e)}")
# Footer
st.markdown("---")
st.caption("AI Video Maker - Powered by Gemini, ElevenLabs, HeyGen & YouTube APIs")
