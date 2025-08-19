"""
Fully Automated AI Video Maker
Converts a topic to a YouTube Shorts video using Gemini, ElevenLabs, HeyGen, CapCut/MoviePy, and YouTube APIs
"""

import streamlit as st
import os
import docx
import requests

# Page config and custom CSS (copied from example)
st.set_page_config(
    page_title="AI Video Maker",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    .stApp {
        background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2a2a6e 100%);
        color: #e0e0ff;
    }
    .main-header {
        background: linear-gradient(135deg, rgba(0,255,255,0.1) 0%, rgba(128,0,255,0.1) 100%);
        border: 1px solid rgba(0,255,255,0.3);
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Grotesk', sans-serif;
    }
    .main-header p {
        color: #a0a0ff;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Fully Automated AI Video Maker</h1>
    <p>Generate YouTube Shorts from a topic using Gemini, ElevenLabs, HeyGen, CapCut/MoviePy, and YouTube APIs</p>
</div>
""", unsafe_allow_html=True)

# API keys from Streamlit secrets
gemini_api_key = st.secrets["gemini_api"] if "gemini_api" in st.secrets else None
elevenlab_api_key = st.secrets["elevenlab_api"] if "elevenlab_api" in st.secrets else None

# Other API keys (entered in UI)
youtube_api_key = st.text_input("YouTube Data API Key", type="password", help="Required for uploading video")
heygen_api_key = st.text_input("HeyGen API Key", type="password", help="Required for avatar video generation")

# Step 1: Topic Input
st.subheader("Video Topic")
topic = st.text_input("Enter your video topic:")

# Step 2: Script Generation (Gemini)
st.subheader("Script Generation (Gemini API)")

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
    # This is a placeholder for Gemini API call
    # Replace with actual Gemini API endpoint and payload
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
        # Gemini returns generated text in result['candidates'][0]['content']['parts'][0]['text']
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "[Error: Unexpected Gemini API response format]"
    else:
        return f"[Error: Gemini API returned {response.status_code}]"

if st.button("Generate Script", disabled=not topic):
    with st.spinner("Generating script with Gemini API..."):
        prompt = load_prompt()
        samples = load_sample_scripts()
        script = generate_script_gemini(topic, prompt, samples, gemini_api_key)
        st.session_state.generated_script = script
        st.success("Script generated!")
    st.text_area("Generated Script", value=script, height=300)

# Step 3: Voice Generation (ElevenLabs)
st.subheader("Voice Generation (ElevenLabs API)")

# ElevenLabs API call
def generate_voice_elevenlabs(script, api_key, voice_id="your_cloned_voice_id"):
    # ElevenLabs API endpoint for TTS
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
        return response.content  # Returns audio bytes
    else:
        st.error(f"ElevenLabs API error: {response.status_code}")
        return None

voice_id = st.text_input("ElevenLabs Voice ID", value="your_cloned_voice_id", help="Enter your ElevenLabs cloned voice ID")

if st.button("Generate Voice", disabled="generated_script" not in st.session_state):
    with st.spinner("Generating voiceover with ElevenLabs API..."):
        script = st.session_state.get("generated_script", "")
        audio_bytes = generate_voice_elevenlabs(script, elevenlab_api_key, voice_id)
        if audio_bytes:
            st.session_state.generated_audio = audio_bytes
            st.success("Voiceover generated!")
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                label="Download Voiceover MP3",
                data=audio_bytes,
                file_name="voiceover.mp3",
                mime="audio/mp3"
            )

# Step 4: AI Video Generation (HeyGen)
st.subheader("AI Video Generation (HeyGen API)")
if st.button("Generate Talking Video", disabled=True):
    st.info("Video generation with HeyGen API will be implemented here.")
    # TODO: Sync generated voice with avatar

# Step 5: Editing Layer (CapCut/MoviePy)
st.subheader("Editing Layer (Subtitles, Transitions, Zoom Cuts)")
if st.button("Edit Video", disabled=True):
    st.info("Editing with CapCut API or MoviePy will be implemented here.")
    # TODO: Auto-generate subtitles, add transitions/emojis/zoom cuts

# Step 6: Upload to YouTube Shorts
st.subheader("Upload to YouTube Shorts")
title = st.text_input("YouTube Title", placeholder="Enter video title...")
description = st.text_area("YouTube Description", placeholder="Enter video description...")
tags = st.text_input("YouTube Tags", placeholder="Comma-separated tags...")
if st.button("Upload to YouTube Shorts", disabled=True):
    st.info("YouTube upload will be implemented here.")
    # TODO: Upload final MP4 to YouTube Shorts

# Footer
st.markdown("""
<div style="text-align: center; color: #888; margin-top:2rem; font-size:0.95rem;">
    Fully Automated AI Video Maker &mdash; Powered by Streamlit, Gemini, ElevenLabs, HeyGen, CapCut, MoviePy, and YouTube APIs
</div>
""", unsafe_allow_html=True)
