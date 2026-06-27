"""
Main application - Lecture Voice-to-Notes Generator
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from utils.audio_handler import AudioHandler
from utils.text_processor import TextProcessor
from utils.note_generator import NoteGenerator
from database import Database
from auth import init_auth, login_ui, require_auth, get_current_user, logout
import google.generativeai as genai

api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="Lecture Voice-to-Notes Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #145a8a;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .flashcard-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

try:
    with open('assets/styles.css', 'r') as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    print("✅ Custom CSS loaded successfully")
except FileNotFoundError:
    print("⚠️ assets/styles.css not found - using default styles")
except Exception as e:
    print(f"⚠️ Error loading CSS: {e}")
# Initialize authentication
init_auth()

# Show login UI and check authentication
if not login_ui():
    st.stop()

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Initialize session state for app
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = None
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None
if 'recording_done' not in st.session_state:
    st.session_state.recording_done = False
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None
if 'api_choice' not in st.session_state:
    st.session_state.api_choice = "gemini"
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'notes' not in st.session_state:
    st.session_state.notes = None
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None
if 'quiz' not in st.session_state:
    st.session_state.quiz = None
if 'current_lecture_id' not in st.session_state:
    st.session_state.current_lecture_id = None

# Main content
st.markdown('<div class="main-header">🎓 Lecture Voice-to-Notes Generator</div>', unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # API Selection
    st.subheader("🤖 AI Model")
    api_choice = st.radio(
        "Choose AI Service:",
        ["Google Gemini", "OpenAI (GPT-3.5)"],
        index=0
    )
    st.session_state.api_choice = "gemini" if "Gemini" in api_choice else "openai"
    
    st.divider()
    
    # API Key input
    if st.session_state.api_choice == "openai":
        st.subheader("🔑 OpenAI API Key")
        api_key = st.text_input("Enter OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API Key set!")
    else:
        st.subheader("🔑 Gemini API Key")
        api_key = st.text_input("Enter Gemini API Key", type="password")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            st.success("✅ API Key set!")
            
            # Test connection
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content("Test")
                st.success("✅ Connection successful!")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)[:100]}")
        else:
            env_key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
            if env_key:
                os.environ["GEMINI_API_KEY"] = env_key
                st.info("ℹ️ Using key from .env file")
            else:
                st.warning("⚠️ Please enter your API key")
    
    st.divider()
    
    # Generation settings
    st.subheader("📝 Generation Settings")
    summary_style = st.selectbox(
        "Summary Style",
        ["concise", "detailed", "executive"],
        index=0
    )
    num_flashcards = st.slider("Number of Flashcards", 5, 20, 10)
    num_quiz_questions = st.slider("Number of Quiz Questions", 3, 10, 5)
    
    st.divider()
    
    # User info
    if st.session_state.authenticated:
        st.markdown(f"👤 **User:** {st.session_state.username}")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

# Audio Input Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-header">📤 Upload or Record Lecture</div>', unsafe_allow_html=True)
    
    input_method = st.radio(
        "Select input method:",
        ["Upload Audio File", "Upload Audio File"],
        horizontal=True
    )
    
    audio_handler = AudioHandler()
    
    if input_method == "Upload Audio File":
        uploaded_file = st.file_uploader(
            "📁 Upload audio file (WAV, MP3, M4A, etc.)",
            type=['wav', 'mp3', 'm4a', 'ogg', 'flac']
        )
        
        if uploaded_file:
            st.audio(uploaded_file, format='audio/wav')
            with st.spinner("⏳ Processing audio..."):
                temp_path = audio_handler.convert_to_wav(uploaded_file)
                if temp_path:
                    st.session_state.audio_file_path = temp_path
                    st.session_state.recording_done = True
                    with open(temp_path, 'rb') as f:
                        st.session_state.audio_bytes = f.read()
                    st.success("✅ Audio processed successfully!")
    
    #else:
        #col_rec1, col_rec2 = st.columns([1, 1])
        #with col_rec1:
           #duration = st.slider("⏱️ Recording duration (seconds)", 5, 120, 30)
        #with col_rec2:
           # if st.button("🎤 Start Recording", type="primary", use_container_width=True):
                #with st.spinner(f"⏳ Recording for {duration} seconds..."):
                    # audio_path = audio_handler.record_audio(duration)
                    #if audio_path:
                        #st.session_state.audio_file_path = audio_path
                        #st.session_state.recording_done = True
                        #with open(audio_path, 'rb') as f:
                         #   st.session_state.audio_bytes = f.read()
                        #st.success("✅ Recording complete!")
        
        if st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format='audio/wav')

with col2:
    st.markdown('<div class="section-header">📝 Transcription</div>', unsafe_allow_html=True)
    
    if st.session_state.recording_done and st.session_state.audio_file_path:
        if st.button("🔊 Transcribe Audio", type="primary", use_container_width=True):
            with st.spinner("⏳ Transcribing audio..."):
                if os.path.exists(st.session_state.audio_file_path):
                    text = audio_handler.transcribe_audio(st.session_state.audio_file_path)
                    if text:
                        st.session_state.transcribed_text = text
                        
                        # Save to database
                        db = st.session_state.db
                        lecture_id = db.save_lecture(
                            user_id=st.session_state.user_id,
                            transcript=text,
                            title=f"Lecture {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            #duration=duration if 'duration' in locals() else None
                        )
                        st.session_state.current_lecture_id = lecture_id
                        db.log_usage(st.session_state.user_id, "transcribe_audio")
                        
                        st.success("✅ Transcription complete!")
                    else:
                        st.error("❌ Failed to transcribe audio")
                else:
                    st.error("❌ Audio file not found")
    
    if st.session_state.transcribed_text:
        text_processor = TextProcessor()
        cleaned_text = text_processor.clean_text(st.session_state.transcribed_text)
        
        with st.expander("📄 View Transcription", expanded=True):
            st.markdown(f'<div class="success-box">{cleaned_text}</div>', unsafe_allow_html=True)
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text)
            st.caption(f"📊 Text Statistics: {word_count} words | {char_count} characters")

# Note Generation Section
if st.session_state.transcribed_text:
    st.divider()
    st.markdown('<div class="section-header">📚 Generate Study Materials</div>', unsafe_allow_html=True)
    
    api_key = st.secrets["GEMINI_API_KEY"] or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("⚠️ Please enter your API key in the sidebar")
    else:
        try:
            note_generator = NoteGenerator(api_type=st.session_state.api_choice)
            
            if hasattr(note_generator, 'model_name') and note_generator.model_name:
                st.info(f"🤖 Using AI Model: {note_generator.model_name}")
            
            col_gen1, col_gen2, col_gen3, col_gen4 = st.columns(4)
            
            # Summary
            with col_gen1:
                if st.button("📝 Generate Summary", use_container_width=True):
                    with st.spinner("⏳ Generating summary..."):
                        try:
                            summary = note_generator.generate_summary(
                                st.session_state.transcribed_text,
                                style=summary_style
                            )
                            if summary and "Error" not in summary:
                                st.session_state.summary = summary
                                
                                # Save to database
                                if st.session_state.current_lecture_id:
                                    db = st.session_state.db
                                    db.save_study_material(
                                        st.session_state.current_lecture_id,
                                        'summary',
                                        {'summary': summary}
                                    )
                                    db.log_usage(st.session_state.user_id, "generate_summary")
                                
                                st.success("✅ Summary generated!")
                            else:
                                st.error(f"❌ Failed to generate summary")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            # Notes
            with col_gen2:
                if st.button("📓 Generate Notes", use_container_width=True):
                    with st.spinner("⏳ Generating study notes..."):
                        try:
                            notes = note_generator.generate_notes(
                                st.session_state.transcribed_text
                            )
                            if notes:
                                st.session_state.notes = notes
                                
                                if st.session_state.current_lecture_id:
                                    db = st.session_state.db
                                    db.save_study_material(
                                        st.session_state.current_lecture_id,
                                        'notes',
                                        notes
                                    )
                                    db.log_usage(st.session_state.user_id, "generate_notes")
                                
                                st.success("✅ Notes generated!")
                            else:
                                st.error("❌ Failed to generate notes")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            # Flashcards
            with col_gen3:
                if st.button("🃏 Generate Flashcards", use_container_width=True):
                    with st.spinner("⏳ Generating flashcards..."):
                        try:
                            flashcards = note_generator.generate_flashcards(
                                st.session_state.transcribed_text,
                                num_cards=num_flashcards
                            )
                            if flashcards:
                                st.session_state.flashcards = flashcards
                                
                                if st.session_state.current_lecture_id:
                                    db = st.session_state.db
                                    db.save_study_material(
                                        st.session_state.current_lecture_id,
                                        'flashcards',
                                        flashcards
                                    )
                                    db.log_usage(st.session_state.user_id, "generate_flashcards")
                                
                                st.success("✅ Flashcards generated!")
                            else:
                                st.error("❌ Failed to generate flashcards")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            # Quiz
            with col_gen4:
                if st.button("📊 Generate Quiz", use_container_width=True):
                    with st.spinner("⏳ Generating quiz..."):
                        try:
                            quiz = note_generator.generate_quiz(
                                st.session_state.transcribed_text,
                                num_questions=num_quiz_questions
                            )
                            if quiz:
                                st.session_state.quiz = quiz
                                
                                if st.session_state.current_lecture_id:
                                    db = st.session_state.db
                                    db.save_study_material(
                                        st.session_state.current_lecture_id,
                                        'quiz',
                                        quiz
                                    )
                                    db.log_usage(st.session_state.user_id, "generate_quiz")
                                
                                st.success("✅ Quiz generated!")
                            else:
                                st.error("❌ Failed to generate quiz")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Failed to initialize AI: {str(e)}")
            st.info("💡 Make sure your API key is correct and has proper permissions.")

# Display Generated Content
if st.session_state.get('summary'):
    st.markdown("### 📝 Summary")
    st.markdown(f'<div class="feature-card">{st.session_state.summary}</div>', unsafe_allow_html=True)

if st.session_state.get('notes'):
    st.markdown("### 📓 Study Notes")
    notes = st.session_state.notes
    if isinstance(notes, dict):
        for key, value in notes.items():
            st.markdown(f"**{key.replace('_', ' ').title()}:**")
            if isinstance(value, list):
                for item in value:
                    st.write(f"- {item}")
            else:
                st.write(value)
            st.markdown("---")
    else:
        st.write(notes)

# In app.py - Update the display section

if st.session_state.get('flashcards'):
    st.markdown("### 🃏 Flashcards")
    flashcards = st.session_state.flashcards
    
    if flashcards and isinstance(flashcards, list) and len(flashcards) > 0:
        # Display in a grid
        cols = st.columns(2)
        for idx, card in enumerate(flashcards):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="flashcard-container">
                    <strong>❓ {card.get('question', 'Question')}</strong>
                    <div style="margin-top: 10px; padding: 8px; background-color: #f0f8f0; border-radius: 5px;">
                        ✅ {card.get('answer', 'Answer')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No flashcards generated. Please try again.")

if st.session_state.get('quiz'):
    st.markdown("### 📊 Quiz")
    quiz = st.session_state.quiz
    
    if quiz and isinstance(quiz, list) and len(quiz) > 0:
        score = 0
        answered = 0
        for idx, q in enumerate(quiz, 1):
            st.markdown(f"**Question {idx}:** {q.get('question', 'Question')}")
            options = q.get('options', [])
            if options:
                selected = st.radio(
                    f"Select answer for Q{idx}:",
                    options,
                    key=f"quiz_{idx}",
                    index=None
                )
                if selected:
                    answered += 1
                    if selected == q.get('correct_answer'):
                        st.success("✅ Correct!")
                        score += 1
                    else:
                        st.error("❌ Incorrect!")
                        st.info(f"💡 Correct answer: {q.get('correct_answer')}")
            st.markdown("---")
        if answered > 0:
            st.info(f"📊 Your score: {score}/{answered} ({int(score/answered*100 if answered > 0 else 0)}%)")
    else:
        st.info("No quiz generated. Please try again.")

# Download options
if st.session_state.transcribed_text:
    st.divider()
    st.markdown('<div class="section-header">💾 Download Materials</div>', unsafe_allow_html=True)
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.download_button(
            label="📥 Download Transcription",
            data=st.session_state.transcribed_text,
            file_name="lecture_transcription.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_d2:
        combined_content = f"""
        ========================================
        LECTURE TRANSCRIPTION
        ========================================
        {st.session_state.transcribed_text}
        """
        if st.session_state.get('summary'):
            combined_content += f"\n\n{'='*40}\nSUMMARY\n{'='*40}\n{st.session_state.summary}"
        if st.session_state.get('notes'):
            combined_content += f"\n\n{'='*40}\nSTUDY NOTES\n{'='*40}\n{st.session_state.notes}"
        
        st.download_button(
            label="📚 Download All Materials",
            data=combined_content,
            file_name="study_materials.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_d3:
        if st.button("🔄 Clear All", use_container_width=True):
            for key in ['transcribed_text', 'summary', 'notes', 'flashcards', 'quiz', 
                       'audio_file_path', 'audio_bytes']:
                if key in st.session_state:
                    st.session_state[key] = None
            st.session_state.recording_done = False
            st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        Built with ❤️ using Streamlit | Lecture Voice-to-Notes Generator
        <br>
        <small>AI-powered study assistant with user authentication</small>
    </div>
""", unsafe_allow_html=True)