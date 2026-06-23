import json
import re
import streamlit as st
import pandas as pd
import google.generativeai as genai
from sklearn.cluster import KMeans
from collections import Counter
from config import GEMINI_MODEL, build_event_extraction_prompt

def _init_gemini():
    """Configure Gemini client once per session."""
    if "gemini_configured" not in st.session_state:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        st.session_state.gemini_configured = True

def get_event_model():
    """Return cached GenerativeModel instance for event extraction."""
    _init_gemini()
    if "gemini_event_model" not in st.session_state:
        st.session_state.gemini_event_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.1,  # Low temp for structured JSON
                "max_output_tokens": 2048,
            },
        )
    return st.session_state.gemini_event_model

def extract_events_to_json(text: str) -> list[dict]:
    """Pass 1: Extract events and thematic roles into JSON."""
    model = get_event_model()
    prompt = build_event_extraction_prompt() + "\n" + text
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Try to parse JSON. Sometimes LLM adds markdown blocks.
        match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            
        events = json.loads(content)
        if isinstance(events, list):
            return events
        return []
    except Exception as e:
        st.error(f"Error extracting events: {e}")
        return []

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Pass 2: Generate embeddings for texts using Gemini."""
    _init_gemini()
    if not texts:
        return []
    try:
        # Using text-embedding-004 which has excellent multilingual support
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="clustering"
        )
        return result['embedding']
    except Exception as e:
        st.error(f"Error embedding texts: {e}")
        return []

def process_events(text: str, max_clusters: int = 3) -> pd.DataFrame:
    """End-to-End Pipeline: Extract -> Embed -> Cluster."""
    # 1. Extract JSON
    events = extract_events_to_json(text)
    if not events:
        return pd.DataFrame()
        
    df = pd.DataFrame(events)
    
    # Fill missing thematic roles
    for col in ['Agent', 'Predicate', 'Theme']:
        if col not in df.columns:
            df[col] = None
    df.fillna("-", inplace=True)
    
    # 2. Prepare text for embedding (Combine Agent + Predicate + Theme)
    combined_texts = []
    for _, row in df.iterrows():
        parts = [str(row.get(c, "")) for c in ['Agent', 'Predicate', 'Theme'] if row.get(c, "") and row.get(c, "") != "-"]
        combined_texts.append(" ".join(parts))
        
    df['Combined_Text'] = combined_texts
    
    # 3. Generate Embeddings
    embeddings = embed_texts(combined_texts)
    
    # Determine safe number of clusters
    n_events = len(embeddings)
    n_clusters = min(max_clusters, n_events)
    
    if n_events < 2 or not embeddings:
        # Not enough data for meaningful clustering
        if n_events > 0:
            df['Cluster'] = 0
            df['Probability'] = 1.0
        return df
        
    # 4. Cluster with KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    df['Cluster'] = kmeans.fit_predict(embeddings)
    
    # 5. Calculate probabilities (Frequency of cluster) to find anomalies
    cluster_counts = Counter(df['Cluster'])
    total_events = len(df)
    
    # Lower probability = more "strange" / anomalous
    df['Probability'] = df['Cluster'].apply(lambda c: cluster_counts[c] / total_events)
    
    # Sort so anomalies (lowest probability) are highlighted
    df = df.sort_values(by=['Probability', 'Cluster'], ascending=[True, True])
    
    return df
