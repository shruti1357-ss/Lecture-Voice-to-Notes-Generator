"""
Database module with user authentication and data persistence
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import bcrypt
import streamlit as st
import pandas as pd

class Database:
    def __init__(self, db_path="lecture_notes.db"):
        """Initialize database connection and create tables"""
        self.db_path = db_path
        self._create_tables()
    
    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """Create all necessary tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table with authentication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    api_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # User sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Lectures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lectures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    transcript TEXT NOT NULL,
                    file_name TEXT,
                    duration INTEGER,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Study materials table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS study_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lecture_id INTEGER NOT NULL,
                    material_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE
                )
            ''')
            
            # Usage log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # API keys storage (for user's saved keys)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    # ---------- AUTHENTICATION METHODS ----------
    
    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create a new user with hashed password"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate user and return user ID if successful"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            user = cursor.fetchone()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user['id'],)
                )
                conn.commit()
                return user['id']
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information by username"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def update_user_api_key(self, user_id: int, provider: str, api_key: str):
        """Save user's API key"""
        # In production, encrypt the key before storing
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_api_keys (user_id, provider, encrypted_key) VALUES (?, ?, ?)",
                (user_id, provider, api_key)
            )
            conn.commit()
    
    def get_user_api_key(self, user_id: int, provider: str) -> Optional[str]:
        """Retrieve user's API key"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT encrypted_key FROM user_api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            result = cursor.fetchone()
            return result['encrypted_key'] if result else None
    
    # ---------- DATA STORAGE METHODS ----------
    
    def save_lecture(self, user_id: int, transcript: str, title: str = None,
                    file_name: str = None, duration: int = None) -> int:
        """Save a lecture transcript"""
        word_count = len(transcript.split())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lectures (user_id, title, transcript, file_name, duration, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title or f"Lecture {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                  transcript, file_name, duration, word_count))
            conn.commit()
            return cursor.lastrowid
    
    def save_study_material(self, lecture_id: int, material_type: str, content: Any):
        """Save generated study materials"""
        content_json = json.dumps(content)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO study_materials (lecture_id, material_type, content)
                VALUES (?, ?, ?)
            ''', (lecture_id, material_type, content_json))
            conn.commit()
            return cursor.lastrowid
    
    def get_lecture(self, lecture_id: int) -> Optional[Dict]:
        """Get a single lecture by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM lectures WHERE id = ?",
                (lecture_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_lecture_materials(self, lecture_id: int) -> List[Dict]:
        """Get all materials for a lecture"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM study_materials WHERE lecture_id = ? ORDER BY created_at",
                (lecture_id,)
            )
            results = cursor.fetchall()
            materials = []
            for row in results:
                material = dict(row)
                material['content'] = json.loads(material['content'])
                materials.append(material)
            return materials
    
    def get_user_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's lecture history with materials"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    l.id as lecture_id,
                    l.title,
                    l.transcript,
                    l.created_at,
                    l.word_count,
                    l.duration,
                    COUNT(sm.id) as material_count
                FROM lectures l
                LEFT JOIN study_materials sm ON l.id = sm.lecture_id
                WHERE l.user_id = ?
                GROUP BY l.id
                ORDER BY l.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """Get user statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total lectures
            cursor.execute(
                "SELECT COUNT(*) FROM lectures WHERE user_id = ?",
                (user_id,)
            )
            total_lectures = cursor.fetchone()[0]
            
            # Total words
            cursor.execute(
                "SELECT SUM(word_count) FROM lectures WHERE user_id = ?",
                (user_id,)
            )
            total_words = cursor.fetchone()[0] or 0
            
            # Materials by type
            cursor.execute('''
                SELECT sm.material_type, COUNT(*) 
                FROM study_materials sm
                JOIN lectures l ON sm.lecture_id = l.id
                WHERE l.user_id = ?
                GROUP BY sm.material_type
            ''', (user_id,))
            materials_by_type = dict(cursor.fetchall())
            
            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM lectures
                WHERE user_id = ? AND created_at >= DATE('now', '-7 days')
                GROUP BY DATE(created_at)
            ''', (user_id,))
            recent_activity = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_lectures': total_lectures,
                'total_words': total_words,
                'materials_by_type': materials_by_type,
                'recent_activity': recent_activity,
                'summary_count': materials_by_type.get('summary', 0),
                'notes_count': materials_by_type.get('notes', 0),
                'flashcards_count': materials_by_type.get('flashcards', 0),
                'quiz_count': materials_by_type.get('quiz', 0)
            }
    
    def log_usage(self, user_id: int, action: str, details: str = None):
        """Log user actions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, action, details)
            )
            conn.commit()
    
    def delete_lecture(self, lecture_id: int, user_id: int) -> bool:
        """Delete a lecture (only if it belongs to user)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM lectures WHERE id = ? AND user_id = ?",
                (lecture_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0