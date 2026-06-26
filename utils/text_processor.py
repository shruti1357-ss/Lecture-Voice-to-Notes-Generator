"""
Text Processor Module - Handles text cleaning, analysis, and processing
"""

import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import textstat
from datetime import datetime
import streamlit as st

class TextProcessor:
    def __init__(self):
        """Initialize text processor with NLTK data"""
        try:
            # Download required NLTK data
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            st.info("📥 Downloading NLTK data (first time setup)...")
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
    
    def clean_text(self, text):
        """
        Clean and preprocess transcribed text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Fix common transcription errors
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common filler words
        text = re.sub(r' um ', ' ', text)
        text = re.sub(r' uh ', ' ', text)
        text = re.sub(r' like ', ' ', text)
        
        # Capitalize first letter of sentences
        text = re.sub(r'(\.\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Ensure first letter is capitalized
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def detect_language(self, text):
        """
        Detect language of the text
        """
        try:
            from langdetect import detect
            return detect(text)
        except:
            return 'en'
    
    def get_readability_score(self, text):
        """
        Calculate readability score (Flesch Reading Ease)
        """
        try:
            score = textstat.flesch_reading_ease(text)
            return round(score, 2)
        except:
            return 0.0
    
    def get_readability_level(self, score):
        """
        Get readability level based on Flesch score
        """
        if score >= 90:
            return "Very Easy (5th grade)"
        elif score >= 80:
            return "Easy (6th grade)"
        elif score >= 70:
            return "Fairly Easy (7th grade)"
        elif score >= 60:
            return "Standard (8th-9th grade)"
        elif score >= 50:
            return "Fairly Difficult (10th-12th grade)"
        elif score >= 30:
            return "Difficult (College)"
        else:
            return "Very Difficult (Graduate)"
    
    def get_text_statistics(self, text):
        """
        Get comprehensive text statistics
        """
        if not text:
            return {}
        
        # Basic statistics
        word_count = len(text.split())
        char_count = len(text)
        sentences = sent_tokenize(text)
        sentence_count = len(sentences)
        
        # Average word length
        words = word_tokenize(text)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Reading time (average 200 words per minute)
        reading_time = word_count / 200.0
        
        # Readability
        readability_score = self.get_readability_score(text)
        readability_level = self.get_readability_level(readability_score)
        
        # Language
        language = self.detect_language(text)
        
        # Key topics
        topics = self.extract_key_topics(text, 5)
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'sentence_count': sentence_count,
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'reading_time_minutes': round(reading_time, 2),
            'readability_score': readability_score,
            'readability_level': readability_level,
            'language': language,
            'key_topics': topics,
            'text_preview': text[:300] + ('...' if len(text) > 300 else '')
        }
    
    def summarize_text(self, text, max_sentences=5):
        """
        Generate a simple extractive summary
        """
        if not text:
            return ""
        
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on word frequency
        words = re.findall(r'\b[a-z]+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score sentences
        sentence_scores = []
        for sentence in sentences:
            score = 0
            words_in_sentence = re.findall(r'\b[a-z]+\b', sentence.lower())
            for word in words_in_sentence:
                if word in word_freq:
                    score += word_freq[word]
            sentence_scores.append((sentence, score))
        
        # Sort by score and get top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
        
        # Maintain original order
        summary = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary.append(sentence)
        
        return ' '.join(summary)
    
    def format_for_export(self, text, title=None):
        """
        Format text for export (download)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted = f"""
{'='*60}
LECTURE NOTES
{'='*60}

"""
        if title:
            formatted += f"Title: {title}\n"
        
        formatted += f"Generated: {timestamp}\n"
        formatted += f"{'-'*60}\n\n"
        formatted += text
        formatted += f"\n\n{'='*60}\nEnd of Notes\n{'='*60}"
        
        return formatted
    
    def segment_text(self, text, max_length=1000):
        """
        Segment text into smaller chunks for processing
        """
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def remove_stopwords(self, text):
        """
        Remove stopwords from text
        """
        try:
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text)
            filtered_words = [word for word in words if word.lower() not in stop_words]
            return ' '.join(filtered_words)
        except:
            return text