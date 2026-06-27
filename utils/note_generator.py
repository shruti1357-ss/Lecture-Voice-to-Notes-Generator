import openai
import google.generativeai as genai
import os
from typing import Dict, List
import json
import time
import re
from datetime import datetime

class NoteGenerator:
    def __init__(self, api_type="gemini"):
        self.api_type = api_type
        self.model = None
        self.model_name = None
        self.last_request_time = None
        
        if api_type == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OpenAI API key not found!")
                
        elif api_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                api_key = os.environ.get("GEMINI_API_KEY")
            
            if not api_key:
                raise ValueError("Gemini API key not found!")
            
            genai.configure(api_key=api_key)
            
            # Auto-discover models
            available_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
            
            if not available_models:
                raise ValueError("No generative models found!")
            
            # Find working model
            for model_name in available_models:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    response = test_model.generate_content("Test")
                    if response and response.text:
                        self.model = test_model
                        self.model_name = model_name
                        print(f"✅ Using model: {model_name}")
                        break
                except:
                    continue
            
            if not self.model:
                self.model = genai.GenerativeModel(available_models[0])
                self.model_name = available_models[0]
                print(f"⚠️ Using fallback model: {available_models[0]}")
    
    def _check_rate_limit(self):
        """Simple rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < 1:
                time.sleep(1 - elapsed)
        self.last_request_time = datetime.now()
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response using selected API"""
        self._check_rate_limit()
        
        try:
            if self.api_type == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful educational assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.api_type == "gemini":
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text
                else:
                    return "Error: Empty response from Gemini"
        
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return "RATE_LIMIT_ERROR"
            return f"Error: {error_msg}"
    
    def generate_summary(self, text: str, style: str = "concise") -> str:
        """Generate summary of the lecture content"""
        prompts = {
            "concise": "Provide a concise summary in bullet points:",
            "detailed": "Provide a detailed summary with key concepts:",
            "executive": "Provide an executive summary with main takeaways:"
        }
        prompt = f"{prompts.get(style, prompts['concise'])}\n\nText: {text[:3000]}"
        
        response = self._generate_response(prompt)
        if response == "RATE_LIMIT_ERROR":
            return "⚠️ Rate limit reached. Please try again later or use a different API key."
        return response
    
    def generate_notes(self, text: str) -> Dict[str, str]:
        """Generate structured study notes"""
        prompt = f"""
        Create structured study notes from this content. Include:
        1. Main Topics
        2. Key Definitions
        3. Important Examples
        4. Key Takeaways
        
        Output as JSON with keys: main_topics, definitions, examples, takeaways
        
        Text: {text[:3000]}
        """
        
        response = self._generate_response(prompt)
        if response == "RATE_LIMIT_ERROR":
            return {"notes": "⚠️ Rate limit reached. Please try again later."}
        
        try:
            return json.loads(response)
        except:
            # Return structured notes even if JSON parsing fails
            return {
                "main_topics": ["Unable to parse structured data"],
                "definitions": ["Please try again"],
                "examples": ["No examples available"],
                "takeaways": [response[:200] + "..."]
            }
    
    def generate_flashcards(self, text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from lecture content - GUARANTEED TO RETURN SOMETHING"""
        try:
            # Try API generation first
            text_chunk = text[:1500] if len(text) > 1500 else text
            
            prompt = f"""
            Create {num_cards} flashcards from this text.
            Each flashcard must have 'question' and 'answer'.
            Output ONLY JSON array.
            FORMAT: [{{"question": "What is X?", "answer": "X is Y"}}]
            
            TEXT: {text_chunk}
            """
            
            response = self._generate_response(prompt)
            
            if response and response != "RATE_LIMIT_ERROR":
                # Try to parse JSON
                try:
                    # Clean response - find JSON array
                    json_match = re.search(r'\[[\s\S]*\]', response)
                    if json_match:
                        flashcards = json.loads(json_match.group())
                        if isinstance(flashcards, list) and len(flashcards) > 0:
                            # Validate each card
                            valid_cards = []
                            for card in flashcards:
                                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                                    valid_cards.append(card)
                            if valid_cards:
                                return valid_cards
                except:
                    pass
            
            # FALLBACK: Generate flashcards from text manually
            return self._generate_flashcards_from_text(text, num_cards)
            
        except Exception as e:
            print(f"Flashcards Error: {e}")
            return self._generate_flashcards_from_text(text, num_cards)
    
    def _generate_flashcards_from_text(self, text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards manually from text - ALWAYS WORKS"""
        # Clean text and extract sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        if not sentences:
            # If no sentences, create generic cards
            return [
                {"question": "What is the main topic of this lecture?", 
                 "answer": "The lecture discusses important concepts related to the subject."},
                {"question": "What is a key takeaway from this lecture?", 
                 "answer": "Understanding the core concepts is essential for mastering the topic."}
            ]
        
        flashcards = []
        
        # Method 1: Create Q&A from sentences
        for i, sentence in enumerate(sentences[:num_cards]):
            words = sentence.split()
            if len(words) > 3:
                # Create question from sentence
                question_words = words[:3]
                question = f"What is the meaning of: '{' '.join(question_words)}'?"
                answer = sentence[:200]
                flashcards.append({
                    "question": question,
                    "answer": answer
                })
        
        # Method 2: Extract key terms and create cards
        words = re.findall(r'\b[A-Za-z]{5,}\b', text.lower())
        word_counts = {}
        for word in words:
            if word not in ['there', 'their', 'these', 'those', 'would', 'could', 'should', 'because', 'therefore']:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top key terms
        key_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for term, count in key_terms:
            if len(flashcards) < num_cards:
                flashcards.append({
                    "question": f"What is the significance of '{term}'?",
                    "answer": f"'{term}' is discussed in the lecture and appears {count} times, indicating it's an important concept."
                })
        
        # Ensure we have at least some cards
        if not flashcards:
            flashcards = [
                {"question": "What is the main topic?", "answer": text[:200] + "..."},
                {"question": "What are the key concepts?", "answer": "Key concepts are discussed in the lecture material."}
            ]
        
        # Limit to requested number
        return flashcards[:num_cards]
    
    def generate_quiz(self, text: str, num_questions: int = 5) -> List[Dict[str, str]]:
        """Generate quiz questions - GUARANTEED TO RETURN SOMETHING"""
        try:
            # Try API generation first
            text_chunk = text[:1500] if len(text) > 1500 else text
            
            prompt = f"""
            Create {num_questions} multiple-choice questions from this text.
            Each question must have 'question', 'options' (4 options), 'correct_answer'.
            Output ONLY JSON array.
            FORMAT: [{{"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}}]
            
            TEXT: {text_chunk}
            """
            
            response = self._generate_response(prompt)
            
            if response and response != "RATE_LIMIT_ERROR":
                # Try to parse JSON
                try:
                    json_match = re.search(r'\[[\s\S]*\]', response)
                    if json_match:
                        quiz = json.loads(json_match.group())
                        if isinstance(quiz, list) and len(quiz) > 0:
                            valid_questions = []
                            for q in quiz:
                                if (isinstance(q, dict) and 
                                    'question' in q and 
                                    'options' in q and 
                                    isinstance(q['options'], list) and 
                                    len(q['options']) >= 4 and 
                                    'correct_answer' in q):
                                    valid_questions.append(q)
                            if valid_questions:
                                return valid_questions
                except:
                    pass
            
            # FALLBACK: Generate quiz from text manually
            return self._generate_quiz_from_text(text, num_questions)
            
        except Exception as e:
            print(f"Quiz Error: {e}")
            return self._generate_quiz_from_text(text, num_questions)
    
    def _generate_quiz_from_text(self, text: str, num_questions: int = 5) -> List[Dict[str, str]]:
        """Generate quiz manually from text - ALWAYS WORKS"""
        # Extract key terms
        words = re.findall(r'\b[A-Za-z]{5,}\b', text.lower())
        word_counts = {}
        for word in words:
            if word not in ['there', 'their', 'these', 'those', 'would', 'could', 'should', 'because', 'therefore']:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        key_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:num_questions]
        
        if not key_terms:
            # If no key terms, create generic quiz
            return [
                {
                    "question": "What is the main topic of this lecture?",
                    "options": ["Artificial Intelligence", "Machine Learning", "Data Science", "All of the above"],
                    "correct_answer": "All of the above"
                },
                {
                    "question": "What is the key takeaway from this lecture?",
                    "options": ["Understanding core concepts", "Memorizing facts", "Reading textbooks", "Taking notes"],
                    "correct_answer": "Understanding core concepts"
                }
            ]
        
        quiz = []
        for term, count in key_terms:
            # Create question with options
            options = [
                f"It is a key concept in this lecture",
                f"It is briefly mentioned once",
                f"It is not important for this topic",
                f"It is only mentioned in passing"
            ]
            
            # Make one correct answer (the first one)
            quiz.append({
                "question": f"What is the significance of '{term}' in this lecture?",
                "options": options,
                "correct_answer": "It is a key concept in this lecture"
            })
        
        return quiz[:num_questions]