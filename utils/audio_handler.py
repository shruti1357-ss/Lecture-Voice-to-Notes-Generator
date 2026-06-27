"""
Audio Handler Module - Handles audio recording, conversion, and transcription
"""

import speech_recognition as sr
import streamlit as st
import tempfile
import os
from pydub import AudioSegment
import wave
import io
import time

class AudioHandler:
    def __init__(self):
        """Initialize the audio handler with speech recognition"""
        self.recognizer = sr.Recognizer()
        self.supported_formats = ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'aac', 'wma']
        
    def transcribe_audio(self, audio_file):
        """
        Transcribe audio file to text using SpeechRecognition
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file):
                st.error("❌ Audio file not found")
                return None
            
            # Open audio file
            with sr.AudioFile(audio_file) as source:
                # Adjust for ambient noise
                st.info("🔊 Adjusting for background noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Record audio data
                st.info("📝 Listening to audio...")
                audio_data = self.recognizer.record(source)
            
            # Try multiple recognition methods for better accuracy
            st.info("🔄 Processing with Google Speech Recognition...")
            
            try:
                # Primary: Google Speech Recognition (requires internet)
                text = self.recognizer.recognize_google(audio_data)
                if text:
                    st.success("✅ Transcription successful using Google")
                    return text
            except sr.UnknownValueError:
                st.warning("⚠️ Google couldn't understand the audio")
            except sr.RequestError as e:
                st.warning(f"⚠️ Google API error: {e}")
            
            # Fallback 1: Sphinx (offline, less accurate)
            try:
                st.info("🔄 Trying offline recognition (Sphinx)...")
                text = self.recognizer.recognize_sphinx(audio_data)
                if text:
                    st.info("ℹ️ Transcription completed using offline recognition")
                    return text
            except:
                st.warning("⚠️ Sphinx recognition failed")
            
            # Fallback 2: Try with different settings
            try:
                st.info("🔄 Retrying with adjusted settings...")
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.recognizer.record(source)
                
                text = self.recognizer.recognize_google(audio_data)
                if text:
                    st.success("✅ Transcription successful with adjusted settings")
                    return text
            except:
                pass
            
            st.error("❌ All recognition methods failed")
            return None
            
        except Exception as e:
            st.error(f"❌ Error transcribing audio: {str(e)}")
            return None
    
    def convert_to_wav(self, uploaded_file):
        """
        Convert uploaded audio to WAV format for processing
        
        Args:
            uploaded_file: Uploaded file object from Streamlit
            
        Returns:
            str: Path to converted WAV file or None if failed
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Check if already WAV format
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            if file_ext == 'wav':
                return tmp_path
            
            # Convert using pydub
            st.info(f"🔄 Converting {file_ext.upper()} to WAV...")
            
            try:
                audio = AudioSegment.from_file(tmp_path)
                wav_path = tmp_path.replace('.tmp', '.wav')
                audio.export(wav_path, format='wav')
                
                # Clean up temporary file
                os.unlink(tmp_path)
                
                st.success("✅ Conversion complete")
                return wav_path
                
            except Exception as e:
                st.error(f"❌ Conversion failed: {str(e)}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None
                
        except Exception as e:
            st.error(f"❌ Error processing audio: {str(e)}")
            return None

    def record_audio(self, duration=30):
        """
        Record audio from microphone
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            str: Path to recorded WAV file or None if failed
        """
        try:
            import pyaudio
            import wave
            
            # Audio settings
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            st.info(f"🎙️ Recording for {duration} seconds... Speak clearly!")
            
            # Record audio
            frames = []
            progress_bar = st.progress(0)
            
            for i in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
                
                # Update progress
                if i % 10 == 0:
                    progress = (i / (RATE / CHUNK * duration))
                    progress_bar.progress(min(progress, 1.0))
            
            progress_bar.progress(1.0)
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            st.success("✅ Recording complete!")
            
            # Save recording
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                wf = wave.open(tmp_file.name, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()
                return tmp_file.name
                
        except ImportError:
            st.error("❌ PyAudio not installed! Please install: pip install pyaudio")
            st.info("💡 For Windows: pip install pipwin && pipwin install pyaudio")
            return None
        except Exception as e:
            st.error(f"❌ Error recording audio: {str(e)}")
            return None
    
    def get_audio_duration(self, audio_file):
        """
        Get duration of audio file in seconds
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            float: Duration in seconds or None if failed
        """
        try:
            audio = AudioSegment.from_file(audio_file)
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except:
            return None
    
    def get_audio_info(self, audio_file):
        """
        Get information about audio file
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            dict: Audio information or None if failed
        """
        try:
            audio = AudioSegment.from_file(audio_file)
            return {
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'file_size': os.path.getsize(audio_file)
            }
        except:
            return None
    
    def save_uploaded_audio(self, uploaded_file, save_path):
        """
        Save uploaded audio file to disk
        
        Args:
            uploaded_file: Uploaded file object
            save_path: Path to save file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            return True
        except Exception as e:
            st.error(f"❌ Error saving file: {str(e)}")
            return False