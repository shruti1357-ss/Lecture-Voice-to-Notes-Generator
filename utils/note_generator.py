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
    
    def _extract_json(self, text: str):
        """
        Extract JSON from text response (handles markdown, extra text, etc.)
        """
        # Try to find JSON array in the response
        json_pattern = r'\[[\s\S]*\]'
        match = re.search(json_pattern, text)
        
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON with triple backticks
        code_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(code_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        return None
    
    def _get_sample_flashcards(self, text: str) -> List[Dict[str, str]]:
        """Generate sample flashcards from text"""
        # Extract key sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        flashcards = []
        for i, sentence in enumerate(sentences[:5]):
            # Create a question from the sentence
            words = sentence.split()
            if len(words) > 3:
                # Use the first few words as context
                context = ' '.join(words[:3])
                flashcards.append({
                    "question": f"What is the main idea in: '{context}...'?",
                    "answer": sentence[:150] + ("..." if len(sentence) > 150 else "")
                })
        
        if not flashcards:
            flashcards = [{
                "question": "What is the main topic of this lecture?",
                "answer": "The lecture covers important concepts related to the subject matter."
            }]
        
        return flashcards
    
    def _get_sample_quiz(self, text: str) -> List[Dict[str, str]]:
        """Generate sample quiz questions"""
        # Extract key terms
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text)
        key_terms = list(set([w.lower() for w in words if w.lower() not in ['there', 'their', 'these', 'those', 'would', 'could', 'should']]))[:5]
        
        quiz = []
        for term in key_terms:
            quiz.append({
                "question": f"What is the significance of '{term}' in this context?",
                "options": [
                    f"It is a key concept",
                    f"It is briefly mentioned",
                    f"It is not important",
                    f"It is discussed in detail"
                ],
                "correct_answer": f"It is a key concept"
            })
        
        if not quiz:
            quiz = [{
                "question": "What is the main topic of this lecture?",
                "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                "correct_answer": "Topic A"
            }]
        
        return quiz
    
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
                return """
⚠️ **Rate Limit Reached**

You've used all 20 free requests for today. 
The quota resets at midnight Pacific Time.

**Solutions:**
1. ⏰ Wait until midnight for quota reset
2. 🔑 Try using OpenAI instead
3. 💡 Generate only what you need
"""
            return f"Error: {error_msg}"
    
    def generate_summary(self, text: str, style: str = "concise") -> str:
        """Generate summary of the lecture content"""
        prompts = {
            "concise": "Provide a concise summary in bullet points:",
            "detailed": "Provide a detailed summary with key concepts:",
            "executive": "Provide an executive summary with main takeaways:"
        }
        prompt = f"{prompts.get(style, prompts['concise'])}\n\nText: {text[:3000]}"
        return self._generate_response(prompt)
    
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
        try:
            return json.loads(response)
        except:
            return {"notes": response}
    
    def generate_flashcards(self, text: str, num_cards: int = 10) -> List[Dict[str, str]]:
        """Generate flashcards from lecture content"""
        try:
            text_chunk = text[:2000] if len(text) > 2000 else text
            
            prompt = f"""
            Create {num_cards} flashcards from this text.
            
            RULES:
            1. Each flashcard must have a 'question' and 'answer'
            2. Questions should test understanding
            3. Answers should be clear and concise
            4. Output ONLY valid JSON array
            
            FORMAT:
            [{{"question": "What is X?", "answer": "X is Y"}}]
            
            TEXT:
            {text_chunk}
            """
            
            response = self._generate_response(prompt)
            
            flashcards = self._extract_json(response)
            
            if flashcards and isinstance(flashcards, list) and len(flashcards) > 0:
                valid_cards = []
                for card in flashcards:
                    if isinstance(card, dict) and 'question' in card and 'answer' in card:
                        valid_cards.append(card)
                
                if valid_cards:
                    return valid_cards
            
            return self._get_sample_flashcards(text)
            
        except Exception as e:
            print(f"Flashcards Error: {e}")
            return self._get_sample_flashcards(text)
    
    def generate_quiz(self, text: str, num_questions: int = 5) -> List[Dict[str, str]]:
        """Generate quiz questions from lecture content"""
        try:
            text_chunk = text[:2000] if len(text) > 2000 else text
            
            prompt = f"""
            Create {num_questions} multiple-choice questions from this text.
            
            RULES:
            1. Each question must have 'question', 'options' (4 options), and 'correct_answer'
            2. Options should be realistic and challenging
            3. Output ONLY valid JSON array
            
            FORMAT:
            [{{"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}}]
            
            TEXT:
            {text_chunk}
            """
            
            response = self._generate_response(prompt)
            
            quiz = self._extract_json(response)
            
            if quiz and isinstance(quiz, list) and len(quiz) > 0:
                valid_questions = []
                for q in quiz:
                    if (isinstance(q, dict) and 
                        'question' in q and 
                        'options' in q and 
                        isinstance(q['options'], list) and 
                        len(q['options']) == 4 and 
                        'correct_answer' in q):
                        valid_questions.append(q)
                
                if valid_questions:
                    return valid_questions
            
            return self._get_sample_quiz(text)
            
        except Exception as e:
            print(f"Quiz Error: {e}")
            return self._get_sample_quiz(text)