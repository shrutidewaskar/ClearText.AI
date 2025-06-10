import spacy
import wikipediaapi

wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='ClearTextAI/1.0 (shrutidewaskar2701@gmail.com)'
)
nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text)
    return list({chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 3})[:10]

def get_definition(term):
    page = wiki.page(term)
    if page.exists():
        return page.summary.split(".")[0]
    return "Definition not found."

def create_glossary(text):
    keywords = extract_keywords(text)
    return {term: get_definition(term) for term in keywords}
