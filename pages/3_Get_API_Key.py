import streamlit as st

st.set_page_config(page_title="Get API Key", page_icon="🔑")

st.title("🔑 How to Get Your Free Gemini API Key")

st.markdown("""
## 📝 Step-by-Step Guide

### 1️⃣ Go to Google AI Studio
👉 [Click here to open Google AI Studio](https://aistudio.google.com/app/apikey)

### 2️⃣ Sign In
- Use your Google account (FREE!)
- If you don't have one, create it in 2 minutes

### 3️⃣ Create API Key
- Click **"Create API Key"** button
- Give it a name (e.g., "Study Helper")
- Click **"Create"**

### 4️⃣ Copy Your Key
- Copy the key that appears (starts with `AIza...`)
- Keep it private - it's your personal key!

### 5️⃣ Use in App
- Go back to the main page
- Paste your key in the sidebar
- Start generating study materials!

---

## ❓ Frequently Asked Questions

### Why do I need my own key?
- **Free Tier:** 20 requests/day per person
- **Privacy:** Your data stays with you
- **Tracking:** Monitor your own usage

### Is it really free?
✅ Yes! The free tier gives you 20 requests per day.
✅ Perfect for students studying a few lectures daily.
✅ No credit card required.

### What if I run out of requests?
⏰ Wait until midnight Pacific Time (quota resets)
🔄 Create another free key (you can have multiple)

### Is my key safe?
🔒 Yes! Your key stays on your device.
🔒 We never store it on our servers.
🔒 It's only used for your current session.

---

## 🎯 Quick Links
- [Google AI Studio](https://aistudio.google.com/app/apikey)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Rate Limits Explained](https://ai.google.dev/gemini-api/docs/rate-limits)
""")

st.info("💡 After getting your key, go back to the main page and paste it in the sidebar!")