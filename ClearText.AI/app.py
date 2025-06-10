import streamlit as st
import requests

BACKEND_URL = "https://266a-117-228-198-179.ngrok-free.app"

st.set_page_config(page_title="ClearTextAI", layout="wide")
st.title("🧠 ClearTextAI - Simplify & Understand Documents")

text_input = st.text_area("📄 Paste your technical or diplomatic text here:", height=250)

if st.button("🔍 Simplify Document"):
    if text_input.strip():
        with st.spinner("Simplifying..."):
            try:
                # Simplify
                res = requests.post(f"{BACKEND_URL}/simplify", json={"text": text_input})
                if res.status_code == 200:
                    result = res.json().get("simplified", "No result returned.")
                    st.subheader("🪄 Simplified Text")
                    st.write(result)
                else:
                    st.error(f"Backend error {res.status_code}: {res.text}")
                    st.stop()

                # Get Glossary
                res_gloss = requests.post(f"{BACKEND_URL}/glossary", json={"text": text_input})
                if res_gloss.status_code == 200:
                    glossary = res_gloss.json().get("glossary", {})
                    st.subheader("📘 Glossary")
                    if glossary:
                        for term, definition in glossary.items():
                            st.markdown(f"**{term}**: {definition}")
                    else:
                        st.warning("No glossary terms found.")
                else:
                    st.warning("Could not fetch glossary.")
            except Exception as e:
                st.error(f"Error contacting backend: {e}")

        st.success("Done!")

st.markdown("---")
st.subheader("👨‍🏫 Ask Tutor")
user_line = st.text_input("Enter a sentence for simplified explanation:")

if st.button("🎓 Ask"):
    if user_line.strip():
        with st.spinner("Explaining..."):
            try:
                res = requests.post(f"{BACKEND_URL}/ask-tutor", json={"text": user_line})
                if res.status_code == 200:
                    explanation = res.json().get("explanation", "No explanation returned.")
                    st.markdown(f"**Simplified:** {explanation}")
                else:
                    st.error(f"Backend error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Error contacting backend: {e}")
