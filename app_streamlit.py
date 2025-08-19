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
    
    # Enhanced prompt to ensure Roman Urdu output in JSON format
    enhanced_prompt = f"""
{prompt}

IMPORTANT: You MUST write the entire script in ROMAN URDU only. Do not use English except for technical terms that don't have Roman Urdu equivalents.

Examples of Roman Urdu style you should follow:
- "Aaj main aap ko bataunga..."
- "Yeh kya baat hai..."
- "Dekho yaar..."
- "Lagta hai..."
- "Samajh gaye?"

Sample Scripts for Reference:
{samples}

Video Topic: {topic}

CRITICAL: Return the script in this EXACT JSON format:
{{
  "title": "Video title in Roman Urdu",
  "segments": [
    {{
      "start_time": 0,
      "end_time": 10,
      "delay_after": 0,
      "text": "Roman Urdu text for first segment"
    }},
    {{
      "start_time": 10,
      "end_time": 25,
      "delay_after": 1,
      "text": "Roman Urdu text for second segment"
    }}
  ]
}}

Remember: 
- Write ONLY in Roman Urdu with casual, witty tone
- Include proper timing based on your script timestamps
- Add delay_after in seconds for pauses between segments
- Return ONLY the JSON, no extra text before or after
"""
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": enhanced_prompt}
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
                script_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Try to parse as JSON
                import json
                try:
                    # Clean up the response (remove markdown formatting if present)
                    cleaned_text = script_text.strip()
                    if cleaned_text.startswith('```json'):
                        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
                    
                    script_json = json.loads(cleaned_text)
                    return script_json
                except json.JSONDecodeError:
                    return f"[Error: Generated script is not valid JSON - {script_text[:200]}...]"
                    
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

# ElevenLabs API call for single text
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

# Generate voice segments with delays from JSON script
def generate_voice_segments_with_delays(script_json, api_key, voice_id):
    """
    Generate voice segments from JSON script with delays
    Returns list of audio segments with timing information
    """
    try:
        import time
        audio_segments = []
        
        for i, segment in enumerate(script_json.get('segments', [])):
            # Generate voice for this segment
            segment_text = segment.get('text', '')
            
            if segment_text.strip():
                # Generate audio for this segment (silent processing)
                audio_bytes = generate_voice_elevenlabs(segment_text, api_key, voice_id)
                
                if audio_bytes:
                    # Store segment with timing info
                    audio_segments.append({
                        'audio': audio_bytes,
                        'start_time': segment.get('start_time', 0),
                        'end_time': segment.get('end_time', 0),
                        'delay_after': segment.get('delay_after', 0),
                        'text': segment_text
                    })
                    
                    # Add small delay between API calls to avoid rate limiting
                    time.sleep(0.5)
                else:
                    return None
        
        return audio_segments
        
    except Exception as e:
        st.error(f"Error generating voice segments: {str(e)}")
        return None

# Simple audio concatenation without external libraries
def concatenate_audio_segments(audio_segments):
    """
    Simple audio concatenation by joining bytes
    This is a basic approach - for production, consider using proper audio libraries
    """
    try:
        if not audio_segments:
            return None
        
        # For now, just return the first segment as a simple fallback
        # In a production environment, you'd use proper audio processing
        combined_audio = b""
        
        for segment in audio_segments:
            combined_audio += segment['audio']
            
            # Note: This doesn't add actual silence delays
            # It just concatenates the audio files
            
        return combined_audio if combined_audio else audio_segments[0]['audio']
        
    except Exception as e:
        st.error(f"Error concatenating audio: {str(e)}")
        return audio_segments[0]['audio'] if audio_segments else None

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
    col_left, col_center, col_right = st.columns([0.42, 0.2, 0.38])
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
    # Only show dropdowns centered when loaded (no button)
    col_left, col_center, col_right = st.columns([0.3, 0.4, 0.3])
    
    with col_center:
        # Two columns for avatar and voice dropdowns only
        avatar_col, voice_col = st.columns(2)
        
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

# Preview Section: Avatar and Voice Previews (appears after loading)
if voices_loaded and avatars_loaded:
    st.markdown('<div style="margin-top: 50px;"></div>', unsafe_allow_html=True)  # Spacing from first line
    
    # Futuristic styling for preview section
    st.markdown("""
    <style>
    .preview-container {
        background: linear-gradient(135deg, rgba(0,255,255,0.05) 0%, rgba(128,0,255,0.05) 100%);
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        min-height: 250px;
        max-height: 280px;
    }
    .preview-title {
        font-size: 0.95rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 12px;
        text-align: center;
    }
    .preview-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .avatar-image {
        border-radius: 8px;
        border: 2px solid rgba(0,255,255,0.3);
        max-width: 100px;
        max-height: 100px;
    }
    .voice-sample-btn {
        background: linear-gradient(135deg, rgba(0,255,255,0.15) 0%, rgba(128,0,255,0.15) 100%);
        border: 1px solid rgba(0,255,255,0.4);
        color: #ffffff;
        font-weight: 500;
        padding: 6px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.85rem;
    }
    .voice-sample-btn:hover {
        background: linear-gradient(135deg, rgba(0,255,255,0.25) 0%, rgba(128,0,255,0.25) 100%);
        border: 1px solid rgba(0,255,255,0.6);
    }
    .compact-info {
        font-size: 0.85rem;
        line-height: 1.3;
        margin: 3px 0;
    }
    
    /* Style the specific containers */
    [data-testid="column"]:has(.avatar-preview) {
        background: linear-gradient(135deg, rgba(0,255,255,0.05) 0%, rgba(128,0,255,0.05) 100%);
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 5px;
        min-height: 250px;
    }
    
    [data-testid="column"]:has(.voice-preview) {
        background: linear-gradient(135deg, rgba(0,255,255,0.05) 0%, rgba(128,0,255,0.05) 100%);
        border: 1px solid rgba(0,255,255,0.2);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 5px;
        min-height: 250px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_left_preview, col_center_preview, col_right_preview = st.columns([0.1, 0.8, 0.1])
    
    with col_center_preview:
        avatar_preview_col, space_col, voice_preview_col = st.columns([0.45, 0.1, 0.45])
        
        # Avatar Preview Box
        with avatar_preview_col:
            # Create a visible box using st.container with fixed height
            container = st.container(border=True, height=360)
            with container:
                st.markdown('<h4 style="text-align: center; color: #00ffff; margin: 8px 0; font-size: 0.85rem;">🎭 Avatar</h4>', unsafe_allow_html=True)
                
                if st.session_state.get('selected_avatar_id'):
                    # Find selected avatar details
                    selected_avatar_details = None
                    for avatar in st.session_state.get('available_avatars', []):
                        if avatar['avatar_id'] == st.session_state.selected_avatar_id:
                            selected_avatar_details = avatar
                            break
                    
                    if selected_avatar_details:
                        # Compact image display
                        if 'preview_image_url' in selected_avatar_details:
                            col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
                            with col2:
                                st.image(selected_avatar_details['preview_image_url'], 
                                       use_container_width=True)
                        else:
                            st.markdown('<div style="text-align: center; padding: 10px; color: rgba(255,255,255,0.7); font-size: 0.7rem;">📸<br>No Preview</div>', 
                                      unsafe_allow_html=True)
                        
                        # Very compact info
                        st.markdown(f'<div style="font-size: 0.7rem; margin: 2px 0; text-align: center;">{selected_avatar_details["avatar_name"]}</div>', unsafe_allow_html=True)
                        if 'gender' in selected_avatar_details:
                            st.markdown(f'<div style="font-size: 0.65rem; margin: 1px 0; text-align: center; opacity: 0.8;">{selected_avatar_details["gender"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5); font-size: 0.7rem;">Select avatar</div>', 
                                  unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5); font-size: 0.7rem;">Select avatar</div>', 
                              unsafe_allow_html=True)
        
        # Voice Preview Box
        with voice_preview_col:
            # Create a visible box using st.container with fixed height
            container = st.container(border=True, height=360)
            with container:
                st.markdown('<h4 style="text-align: center; color: #00ffff; margin: 8px 0; font-size: 0.85rem;">🎤 Voice</h4>', unsafe_allow_html=True)
                
                if st.session_state.get('selected_voice_id'):
                    # Find selected voice details
                    selected_voice_details = None
                    for voice in st.session_state.get('available_voices', []):
                        if voice['voice_id'] == st.session_state.selected_voice_id:
                            selected_voice_details = voice
                            break
                    
                    if selected_voice_details:
                        # Very compact voice info
                        st.markdown(f'<div style="font-size: 0.7rem; margin: 5px 0; text-align: center;">{selected_voice_details["name"]}</div>', unsafe_allow_html=True)
                        if 'category' in selected_voice_details:
                            st.markdown(f'<div style="font-size: 0.65rem; margin: 3px 0; text-align: center; opacity: 0.8;">{selected_voice_details["category"]}</div>', unsafe_allow_html=True)
                        
                        # Compact spacing
                        st.markdown('<div style="margin: 8px 0;"></div>', unsafe_allow_html=True)
                        
                        # Small voice sample button
                        if st.button("🔊 Test", key="voice_sample", 
                                   help="Generate a sample to hear this voice",
                                   use_container_width=True):
                            with st.spinner("Generating..."):
                                sample_text = "Hello! This is a sample."
                                sample_audio = generate_voice_elevenlabs(
                                    sample_text, 
                                    elevenlab_api_key, 
                                    st.session_state.selected_voice_id
                                )
                                
                                if sample_audio:
                                    st.audio(sample_audio, format="audio/mp3")
                                else:
                                    st.error("Failed to generate sample")
                    else:
                        st.markdown('<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5); font-size: 0.7rem;">Select voice</div>', 
                                  unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5); font-size: 0.7rem;">Select voice</div>', 
                              unsafe_allow_html=True)

# Second line: Topic input and testing buttons (conditional styling)
st.markdown('<div style="margin-top: 80px;"></div>', unsafe_allow_html=True)  # Add 80px padding from first line

# Check if voices and avatars are loaded for conditional styling
content_enabled = voices_loaded and avatars_loaded

col_left, col_center, col_right = st.columns([0.1, 0.8, 0.1])

with col_center:
    # Create columns: topic field, generate script button, generate voice button, create video button, upload video button
    topic_col, script_btn_col, voice_btn_col, video_btn_col, upload_btn_col = st.columns([0.4, 0.15, 0.15, 0.15, 0.15])
    
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
    
    with upload_btn_col:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        upload_video_clicked = st.button(
            "Upload Video", 
            disabled=True,  # Will be enabled when video is created
            key="upload_video"
        )
    
    # Handle Generate Script button click
    if generate_script_clicked and topic:
        try:
            prompt = load_prompt()
            samples = load_sample_scripts()
            script_json = generate_script_gemini(topic, prompt, samples, gemini_api_key)
            st.session_state.generated_script = script_json
            
            # Display generated script
            if isinstance(script_json, dict):
                with st.expander("Generated Script JSON", expanded=True):
                    import json
                    st.json(script_json)
                    
                    # Also show in readable format
                    st.subheader("Readable Format:")
                    st.write(f"**Title:** {script_json.get('title', 'No title')}")
                    
                    for i, segment in enumerate(script_json.get('segments', [])):
                        st.write(f"**({segment.get('start_time', 0)}-{segment.get('end_time', 0)} seconds)**")
                        st.write(f"{segment.get('text', '')}")
                        if segment.get('delay_after', 0) > 0:
                            st.write(f"*[Pause: {segment.get('delay_after')} seconds]*")
                        st.write("---")
            else:
                with st.expander("Generated Script (Error)", expanded=True):
                    st.text_area("Script Content:", value=str(script_json), height=150, key="script_display")
                
        except Exception as e:
            st.error(f"Script generation error: {str(e)}")
    
    # Handle Generate Voice button click
    if generate_voice_clicked and st.session_state.get('generated_script'):
        try:
            voice_id = st.session_state.get('selected_voice_id', 'your_cloned_voice_id')
            script_json = st.session_state.generated_script
            
            if isinstance(script_json, dict):
                with st.spinner("Generating voice segments..."):
                    # Generate individual voice segments
                    audio_segments = generate_voice_segments_with_delays(script_json, elevenlab_api_key, voice_id)
                    
                    if audio_segments:
                        # Store segments for later use
                        st.session_state.generated_audio_segments = audio_segments
                        
                        # Simple concatenation (basic approach)
                        combined_audio = concatenate_audio_segments(audio_segments)
                        
                        if combined_audio:
                            st.session_state.generated_audio = combined_audio
                            st.session_state.audio_ready = True
                        else:
                            st.error("Failed to combine audio segments")
                    else:
                        st.error("Failed to generate voice segments")
            else:
                st.error("Script is not in JSON format. Please regenerate the script.")
                
        except Exception as e:
            st.error(f"Voice generation error: {str(e)}")
    
    # Handle Upload Video button click
    if upload_video_clicked and st.session_state.get('generated_video'):
        try:
            video_path = st.session_state.get('generated_video')
            video_title = st.session_state.get('generated_script', {}).get('title', 'AI Generated Video')
            
            with st.spinner("Uploading to YouTube..."):
                youtube_url = upload_to_youtube(video_path, video_title, youtube_credentials)
                
                if youtube_url:
                    st.success(f"✅ Video uploaded successfully!")
                    st.markdown(f"**YouTube URL:** [Watch Video]({youtube_url})")
                    st.session_state.video_uploaded = True
                else:
                    st.error("Failed to upload video to YouTube")
                    
        except Exception as e:
            st.error(f"Upload error: {str(e)}")

# Third line: Generated Audio Player and Download (futuristic design)
if st.session_state.get('audio_ready', False):
    st.markdown('<div style="margin-top: 60px;"></div>', unsafe_allow_html=True)  # Add padding from second line
    
    # Futuristic styling for audio section
    st.markdown("""
    <style>
    .audio-container {
        background: linear-gradient(135deg, rgba(0,255,255,0.1) 0%, rgba(128,0,255,0.1) 100%);
        border: 1px solid rgba(0,255,255,0.3);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
    }
    .audio-title {
        font-size: 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .download-btn {
        width: 100%;
        background: linear-gradient(135deg, rgba(0,255,255,0.2) 0%, rgba(128,0,255,0.2) 100%);
        border: 1px solid rgba(0,255,255,0.5);
        color: #ffffff;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        padding: 10px 20px;
        border-radius: 6px;
        text-align: center;
        margin-top: 10px;
        transition: all 0.3s ease;
    }
    .download-btn:hover {
        background: linear-gradient(135deg, rgba(0,255,255,0.3) 0%, rgba(128,0,255,0.3) 100%);
        border: 1px solid rgba(0,255,255,0.7);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered layout with equal spacing for third line items
    col_left_audio, col_center_audio, col_right_audio = st.columns([0.05, 0.9, 0.05])
    
    with col_center_audio:
        # Three equal columns with equal spacing
        audio_col, video_col, status_col = st.columns([1, 1, 1])
        
        # Audio Section
        with audio_col:
            # Create a visible box using st.container
            container = st.container(border=True)
            with container:
                st.markdown('<h3 style="text-align: center; color: #00ffff; margin: 8px 0; font-size: 1rem;">🎵 Generated Audio</h3>', unsafe_allow_html=True)
                
                # Audio player
                if st.session_state.get('generated_audio'):
                    st.audio(st.session_state.generated_audio, format="audio/mp3")
                    
                    # Download button
                    import base64
                    audio_b64 = base64.b64encode(st.session_state.generated_audio).decode()
                    href = f'data:audio/mp3;base64,{audio_b64}'
                    
                    st.markdown(f'''
                        <a href="{href}" download="generated_voice_audio.mp3" class="download-btn">
                            💾 Download Audio
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5); font-size: 0.9rem;">Audio will appear here</div>', 
                              unsafe_allow_html=True)
        
        # Video Section (placeholder for now)
        with video_col:
            # Create a visible box using st.container
            container = st.container(border=True)
            with container:
                st.markdown('<h3 style="text-align: center; color: #00ffff; margin: 8px 0; font-size: 1rem;">🎬 Generated Video</h3>', unsafe_allow_html=True)
                
                if st.session_state.get('generated_video'):
                    st.video(st.session_state.generated_video)
                    
                    st.markdown('''
                        <a href="#" class="download-btn">
                            💾 Download Video
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5); font-size: 0.9rem;">Video will appear here</div>', 
                              unsafe_allow_html=True)
        
        # Upload Status Section
        with status_col:
            # Create a visible box using st.container
            container = st.container(border=True)
            with container:
                st.markdown('<h3 style="text-align: center; color: #00ffff; margin: 8px 0; font-size: 1rem;">📤 Upload Status</h3>', unsafe_allow_html=True)
                
                if st.session_state.get('video_uploaded'):
                    st.success("✅ Video uploaded to YouTube!")
                    if st.session_state.get('youtube_url'):
                        st.markdown(f'[🎥 Watch on YouTube]({st.session_state.youtube_url})', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5); font-size: 0.9rem;">Upload status will appear here</div>', 
                              unsafe_allow_html=True)
# Footer
st.markdown("---")
st.caption("AI Video Maker - Powered by Gemini, ElevenLabs, HeyGen & YouTube APIs")
