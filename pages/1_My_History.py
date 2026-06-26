import streamlit as st
from database import Database
from auth import require_auth
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="My History", page_icon="📚")

# Require authentication
if not require_auth():
    st.stop()

st.title("📚 My Study History")

db = st.session_state.db
history = db.get_user_history(st.session_state.user_id, limit=50)

if not history:
    st.info("📖 No lectures saved yet! Go to the main page to start studying.")
else:
    st.success(f"📊 You have {len(history)} saved lectures")
    
    # Display as cards
    for lecture in history:
        with st.expander(f"📖 {lecture['title']}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Date:** {lecture['created_at']}")
                st.write(f"**Words:** {lecture['word_count']:,}")
                st.write(f"**Materials:** {lecture['material_count']}")
                st.write(f"**Preview:** {lecture['transcript'][:200]}...")
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{lecture['lecture_id']}"):
                    if db.delete_lecture(lecture['lecture_id'], st.session_state.user_id):
                        st.success("Deleted!")
                        st.rerun()