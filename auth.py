"""
Authentication module for user management
"""

import streamlit as st
import hashlib
import uuid
from datetime import datetime, timedelta
from database import Database

def init_auth():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'db' not in st.session_state:
        st.session_state.db = Database()

def login(username: str, password: str) -> bool:
    """Login user"""
    db = st.session_state.db
    user_id = db.authenticate_user(username, password)
    
    if user_id:
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.username = username
        
        # Log login
        db.log_usage(user_id, "login")
        return True
    return False

def logout():
    """Logout user"""
    if st.session_state.authenticated:
        db = st.session_state.db
        db.log_usage(st.session_state.user_id, "logout")
    
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()

def register(username: str, email: str, password: str, confirm_password: str) -> tuple:
    """Register a new user"""
    # Validation
    if not username or not email or not password:
        return False, "All fields are required"
    
    if password != confirm_password:
        return False, "Passwords do not match"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    db = st.session_state.db
    
    # Check if username exists
    if db.get_user_by_username(username):
        return False, "Username already exists"
    
    # Create user
    user_id = db.create_user(username, email, password)
    
    if user_id:
        return True, "Registration successful! Please login."
    else:
        return False, "Registration failed. Please try again."

def login_ui():
    """Display login/signup UI"""
    init_auth()
    
    if st.session_state.authenticated:
        return True
    
    st.sidebar.markdown("### 🔐 Authentication")
    
    # Tab selection
    tab1, tab2 = st.sidebar.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("#### Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if login(username, password):
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    with tab2:
        st.markdown("#### Create Account")
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Sign Up", use_container_width=True):
            success, message = register(new_username, new_email, new_password, confirm_password)
            if success:
                st.success("✅ " + message)
            else:
                st.error("❌ " + message)
    
    st.sidebar.divider()
    st.sidebar.info(
        "💡 **Demo Account:**\n"
        "Username: demo\n"
        "Password: demopassword123"
    )
    
    return False

def require_auth():
    """Decorator to require authentication"""
    init_auth()
    if not st.session_state.authenticated:
        st.warning("⚠️ Please login to access this feature")
        return False
    return True

def get_current_user():
    """Get current user info"""
    if st.session_state.authenticated:
        db = st.session_state.db
        return db.get_user_by_id(st.session_state.user_id)
    return None

def show_user_info():
    """Display user info in sidebar"""
    if st.session_state.authenticated:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{st.session_state.username}**")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()