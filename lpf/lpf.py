import gradio as gr
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI


# -----------------------------
# LOAD MODELS AND DATA
# -----------------------------

# embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# load saved embeddings
embeddings = np.load("case_embeddings.npy")

# load processed sections
with open("processed_sections.pkl", "rb") as f:
    all_sections = pickle.load(f)


# OpenAI client
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")


# -----------------------------
# SEMANTIC SEARCH
# -----------------------------

def semantic_search(query, top_n=3):
    query_embedding = model.encode([query])
    scores = cosine_similarity(query_embedding, embeddings).flatten()
    top_indices = scores.argsort()[-top_n:][::-1]

    results = [all_sections[i] for i in top_indices]

    return results


# -----------------------------
# PROMPT GENERATION
# -----------------------------

def generate_prompt(query, sections):

    prompt = "You are a Kenyan Legal Assistant. Answer the question using the tribunal cases provided.\n"
    prompt += "Always cite the case name.\n\n"

    prompt += "--- LEGAL CONTEXT ---\n"

    for sec in sections:
        prompt += f"CASE: {sec.get('case_name','Unknown')}\n"
        prompt += f"SECTION: {sec.get('section_label','')}\n"
        prompt += f"CONTENT: {sec.get('section_content','')}\n\n"

    prompt += f"QUESTION: {query}\n"
    prompt += "ANSWER:"

    return prompt


# -----------------------------
# LLM RESPONSE
# -----------------------------

def legal_chat_response(query, top_n):

    sections = semantic_search(query, top_n)

    prompt = generate_prompt(query, sections)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content

    cited_cases = [
        {
            "case_name": s.get("case_name"),
            "section": s.get("section_label"),
            "date": s.get("decision_date")
        }
        for s in sections
    ]

    return answer, cited_cases


# -----------------------------
# GRADIO INTERFACE
# -----------------------------

iface = gr.Interface(
    fn=legal_chat_response,
    inputs=[
        gr.Textbox(label="Your Question"),
        gr.Slider(1, 5, value=3, step=1, label="Number of Sources")
    ],
    outputs=[
        gr.Textbox(label="Legal Analysis"),
        gr.JSON(label="Cited Sources")
    ],
    title="Kenyan Tribunal & Constitutional Assistant"
)


# launch app
iface.launch(share=True)