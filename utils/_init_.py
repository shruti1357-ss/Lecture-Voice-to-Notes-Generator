"""
Utility Modules for Lecture Voice-to-Notes Generator
"""

# Import main classes for easy access
from .audio_handler import AudioHandler
from .text_processor import TextProcessor
from .note_generator import NoteGenerator

# Define what's available when importing *
__all__ = [
    'AudioHandler',
    'TextProcessor', 
    'NoteGenerator'
]

# Package version
__version__ = '2.0.0'