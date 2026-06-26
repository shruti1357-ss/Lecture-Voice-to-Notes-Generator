import streamlit as st
from database import Database
from auth import require_auth
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Analytics", page_icon="📊")

if not require_auth():
    st.stop()

st.title("📊 Your Learning Analytics")

db = st.session_state.db
stats = db.get_user_statistics(st.session_state.user_id)

# Display metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📝 Total Lectures", stats['total_lectures'])
with col2:
    st.metric("📚 Total Materials", 
              sum(stats['materials_by_type'].values()) if stats['materials_by_type'] else 0)
with col3:
    st.metric("📄 Total Words", f"{stats['total_words']:,}")
with col4:
    st.metric("📊 Materials per Lecture", 
              round(sum(stats['materials_by_type'].values()) / stats['total_lectures'], 1) 
              if stats['total_lectures'] > 0 else 0)

st.divider()

# Materials by type chart
if stats['materials_by_type']:
    st.subheader("📊 Materials by Type")
    df = pd.DataFrame({
        'Type': list(stats['materials_by_type'].keys()),
        'Count': list(stats['materials_by_type'].values())
    })
    fig = px.pie(df, values='Count', names='Type', title='Study Materials Distribution')
    st.plotly_chart(fig, use_container_width=True)

# Recent activity
if stats.get('recent_activity'):
    st.subheader("📈 Recent Activity (Last 7 Days)")
    df_activity = pd.DataFrame(stats['recent_activity'])
    fig = px.line(df_activity, x='date', y='count', title='Lectures per Day')
    st.plotly_chart(fig, use_container_width=True)

# Quick stats
st.subheader("📋 Quick Stats")
col_a, col_b = st.columns(2)
with col_a:
    st.write(f"✅ Summaries: {stats.get('summary_count', 0)}")
    st.write(f"📓 Notes: {stats.get('notes_count', 0)}")
with col_b:
    st.write(f"🃏 Flashcards: {stats.get('flashcards_count', 0)}")
    st.write(f"📊 Quizzes: {stats.get('quiz_count', 0)}")