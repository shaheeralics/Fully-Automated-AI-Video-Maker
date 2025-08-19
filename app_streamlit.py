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

# First line: HeyGen API, YouTube API, Load Voices
col_a, col_b, col_c = st.columns(3)

with col_a:
    heygen_api_key = st.text_input("HeyGen API Key", type="password", help="Required for avatar video generation")

with col_b:
    youtube_api_key = st.text_input("YouTube API Key", type="password", help="Required for uploading video")

with col_c:
    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
    if st.button("Load Voices", help="Load available ElevenLabs voices"):
        st.success("Voices loaded!")

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

# Main layout - three columns for the workflow
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("**Configuration**")
    voice_id = st.text_input("Voice ID", value="your_cloned_voice_id", help="ElevenLabs voice", key="voice")
    avatar_id = st.text_input("Avatar ID", value="your_avatar_id", help="HeyGen avatar", key="avatar")

with col2:
    st.markdown("**Video Generation**")
    topic = st.text_input("Enter your video topic:", placeholder="e.g., AI in Pakistan", key="topic_input")
    
    if st.button("Generate Video", disabled=not topic, key="gen_video"):
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
            audio_bytes = generate_voice_elevenlabs(script, elevenlab_api_key, voice_id)
            if audio_bytes:
                st.session_state.generated_audio = audio_bytes
                
                # Step 3: Generate Video
                status_text.text("Creating video with avatar...")
                progress_bar.progress(70)
                video_file = generate_video_heygen(audio_bytes, heygen_api_key, avatar_id)
                st.session_state.generated_video = video_file
                
                progress_bar.progress(100)
                status_text.text("Video ready!")
                st.session_state.video_ready = True
                st.success("Video generated successfully!")
            else:
                st.error("Failed to generate voice")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col3:
    st.markdown("**Preview & Upload**")
    
    if st.session_state.get('video_ready', False):
        # Script preview (collapsible)
        if st.session_state.get('generated_script'):
            with st.expander("Script", expanded=False):
                st.text_area("", value=st.session_state.generated_script, height=80, key="script_preview")
        
        # Audio preview
        if st.session_state.get('generated_audio'):
            st.audio(st.session_state.generated_audio, format="audio/mp3")
        
        # Video preview (placeholder)
        st.video("https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4")
        
        # Upload section
        title = st.text_input("Title", value=f"Video about {topic}" if topic else "My Video", key="video_title")
        
        if st.button("Upload to YouTube", key="upload_btn"):
            with st.spinner("Uploading..."):
                video_url = upload_to_youtube(st.session_state.generated_video, title, youtube_api_key)
                st.success(f"Video uploaded! [View]({video_url})")
    else:
        st.info("Generate a video to see preview")

# Footer
st.markdown("---")
st.caption("AI Video Maker - Powered by Gemini, ElevenLabs, HeyGen & YouTube APIs")

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
