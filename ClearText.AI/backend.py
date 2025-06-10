from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- LLM and NLP Imports ---
from dotenv import load_dotenv
import os
from google.generativeai import GenerativeModel, configure as genai_configure
import spacy
import wikipediaapi
# --- End LLM and NLP Imports ---

# Load environment variables from .env file at the root of your project
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure Google Generative AI ---
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")
genai_configure(api_key=GEMINI_API_KEY)

# IMPORTANT: Using 'gemini-1.5-flash' for broader compatibility and performance
gemini_model = GenerativeModel('gemini-1.5-flash')
# --- End Google Generative AI Setup ---

# --- Configure SpaCy for NLP (for Glossary) ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "SpaCy model 'en_core_web_sm' not found. "
        "Please run 'python -m spacy download en_core_web_sm' in your terminal."
    )

# Specify a User-Agent for Wikipedia API as a best practice
wiki_wiki = wikipediaapi.Wikipedia(user_agent='ClearTextAI (shrutidewaskar2701@gmail.com)', language='en')
# --- End SpaCy Setup ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "ClearTextAI Backend API is running!"}

@app.post("/simplify")
async def simplify_document(item: TextInput):
    text = item.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Please provide text to simplify.")

    try:
        # Prompt for text simplification
        prompt = (
            "Simplify the following highly technical or diplomatic document for a general audience. "
            "Maintain accuracy but use clear, concise, and plain language. "
            "Focus on the core meaning and eliminate jargon:\n\n"
            f"{text}"
        )
        # Call the Gemini API
        response = await gemini_model.generate_content_async(
            contents=[
                {"role": "user", "parts": [prompt]}
            ],
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        simplified_text = response.text.strip()
        return {"simplified": simplified_text}
    except Exception as e:
        print(f"Error during simplification: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing simplification: {str(e)}")

@app.post("/ask-tutor")
async def ask_tutor_endpoint(item: TextInput):
    text = item.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Please provide a sentence/concept to explain.")

    try:
        # Prompt for explanation from a tutor perspective
        prompt = (
            "As a knowledgeable and patient tutor, explain the following sentence or concept "
            "in simple, easy-to-understand terms for someone learning the topic. "
            "Provide a clear, concise explanation:\n\n"
            f"'{text}'"
        )
        # Call the Gemini API
        response = await gemini_model.generate_content_async(
            contents=[
                {"role": "user", "parts": [prompt]}
            ],
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        explanation = response.text.strip()
        return {"explanation": explanation}
    except Exception as e:
        print(f"Error during ask-tutor: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing tutor request: {str(e)}")

def create_glossary_terms(text: str) -> dict:
    """
    Identifies potential glossary terms using spaCy (Named Entities and Noun Chunks)
    and fetches their definitions from Wikipedia. Improved filtering and length.
    """
    doc = nlp(text)
    glossary = {}
    # Use lemmatized form for tracking to handle singular/plural forms
    processed_lemmas = set() 

    # Common words that might get caught but are usually not good glossary terms
    # Extend this list as needed based on your content.
    common_words_to_exclude = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been", "being",
        "to", "of", "and", "or", "in", "on", "at", "for", "with", "as", "by",
        "from", "this", "that", "these", "those", "it", "its", "which", "who",
        "what", "where", "when", "why", "how", "can", "will", "would", "should"
    }

    # 1. Extract Named Entities (e.g., organizations, people, locations, technical terms if labeled)
    for ent in doc.ents:
        term = ent.text.strip()
        lemma_term = ent.lemma_.lower() # Get the base form of the word

        # Basic filtering for relevant entities, length, and common words
        if len(term) > 1 and lemma_term not in processed_lemmas and \
           lemma_term not in common_words_to_exclude and \
           ent.label_ in ["ORG", "GPE", "PERSON", "NORP", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "TERM"]: # Added "TERM" if your model recognizes it
            
            page_py = wiki_wiki.page(term)
            if page_py.exists():
                # Attempt to get a more concise summary
                summary = page_py.summary.split('\n')[0] # First paragraph/sentence
                if len(summary) > 500: # Increase summary length limit slightly
                    summary = summary[:500] + "..."
                glossary[term] = summary
                processed_lemmas.add(lemma_term)
            # else:
            #     glossary[term] = "Definition not found on Wikipedia." # Option to include 'not found'

    # 2. Extract Noun Chunks (e.g., "technical writing", "consumer electronics")
    for chunk in doc.noun_chunks:
        term = chunk.text.strip()
        lemma_term = chunk.lemma_.lower() # Get the base form of the chunk

        # Filter for terms that are likely multi-word concepts, not single common words,
        # and not already processed.
        if ' ' in term and len(term) > 3 and lemma_term not in processed_lemmas:
            # Further heuristic: require at least one capitalized word in multi-word terms
            # or ensure it's not entirely lowercase common words
            if any(word[0].isupper() for word in term.split()) or \
               all(word.lower() not in common_words_to_exclude for word in term.split()):
                
                page_py = wiki_wiki.page(term)
                if page_py.exists():
                    summary = page_py.summary.split('\n')[0]
                    if len(summary) > 500:
                        summary = summary[:500] + "..."
                    glossary[term] = summary
                    processed_lemmas.add(lemma_term)

    return glossary

@app.post("/glossary")
async def generate_glossary(item: TextInput):
    text = item.text.strip()
    if not text:
        return {"glossary": {}}

    try:
        glossary_terms = create_glossary_terms(text)
        return {"glossary": glossary_terms}
    except Exception as e:
        print(f"Error during glossary generation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating glossary: {str(e)}")

