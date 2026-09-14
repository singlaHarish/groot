import time
import requests

def generate_gemini_response(api_key: str, context: str, query: str) -> str:
    """
    Sends the context and query to Gemini using the REST API.
    """
    if not api_key:
        return "Error: Please provide a Gemini API key."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are an expert assistant helping users understand a document.
Answer the user's query using the provided context excerpts from the document.
The context is a set of the most relevant sections retrieved from the full document.

Guidelines:
- Base your answer primarily on the provided context.
- If the context contains partial information, use it to give the best possible answer.
- If the context is insufficient to fully answer, provide what you can and clearly note what is missing.
- Do NOT refuse to answer if the context contains any relevant information at all.
- Keep your answer concise and focused on the query.

Context (retrieved document sections):
{context}

Query:
{query}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "Error parsing response from Gemini API: " + str(data)
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return f"Error communicating with Gemini API after {max_retries} attempts: {str(e)}"

def generate_gemini_vertex(context: str, query: str) -> str:
    """
    Sends the context and query to Gemini using the google-genai SDK for Vertex AI.
    """
    try:
        from google import genai
    except ImportError:
        return "Error: google-genai library is not installed."
        
    prompt = f"""
You are an expert assistant helping users understand a document.
Answer the user's query using the provided context excerpts from the document.
The context is a set of the most relevant sections retrieved from the full document.

Guidelines:
- Base your answer primarily on the provided context.
- If the context contains partial information, use it to give the best possible answer.
- If the context is insufficient to fully answer, provide what you can and clearly note what is missing.
- Do NOT refuse to answer if the context contains any relevant information at all.
- Keep your answer concise and focused on the query.

Context (retrieved document sections):
{context}

Query:
{query}
"""
    try:
        client = genai.Client(vertexai=True, project="singla", location="europe-west3")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text if response.text is not None else "No response generated from Vertex AI"
    except Exception as e:
        return f"Error communicating with Vertex AI: {str(e)}"
