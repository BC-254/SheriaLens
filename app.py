import streamlit as st
import os
import time
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

st.set_page_config(
    page_title="SheriaLens | AI Legal Assistant",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS design
st.markdown("""
<style>
    .stChatFloatingInputContainer { padding-bottom: 20px; }
    .legal-source-box { 
        background-color: #f8f9fa; 
        border-left: 4px solid #0d6efd; 
        padding: 10px; 
        border-radius: 5px;
        font-size: 0.9em;
        color: #333;
    }
    /* Dark mode support for the source box */
    @media (prefers-color-scheme: dark) {
        .legal-source-box { background-color: #1e1e1e; color: #ddd; }
    }
</style>
""", unsafe_allow_html=True)


# Caching the model and database into server memory
@st.cache_resource(show_spinner=False)
def load_infrastructure():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("API Key missing!")
        st.stop()
        
    genai.configure(api_key=api_key)
    
    # Initializing local embeddings & chromadb 
    emb_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    client = chromadb.PersistentClient(path="./sherialens_db")
    const_col = client.get_collection("constitution")
    case_col = client.get_collection("caselaws")
    
    # Initialize Gemini
    llm = genai.GenerativeModel('gemini-2.5-flash')
    synth = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="""You are SheriaLens, an expert legal AI assistant. 
        Answer the user's question using ONLY the provided legal context. 
        Ground your answer in Constitutional Law first, then use Supporting Case Law. 
        Format your response cleanly using bullet points or bold text where appropriate.
        If the context does not contain the answer, say 'I cannot find this in the database.'"""
    )
    
    return emb_model, const_col, case_col, llm, synth

# Load everything silently before the UI renders
with st.spinner("Initializing SheriaLens Core Infrastructure..."):
    emb_model, const_col, case_col, llm_model, synthesizer = load_infrastructure()



def rewrite_query(user_query, history):
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-4:]])
    prompt = f"""
    You are an expert legal researcher. Look at the recent conversation history and the new user question.
    Resolve any pronouns. Extract the core legal concepts to create a database search query. 
    Do not answer the question, just output the search terms.
    
    Recent Conversation: {history_text if history_text else "None"}
    New Question: {user_query}
    Search Terms:
    """
    response = llm_model.generate_content(prompt)
    return response.text.strip()

def retrieve_context(optimized_query):
    query_vector = emb_model.encode([optimized_query]).tolist()
    const_results = const_col.query(query_embeddings=query_vector, n_results=2)
    case_results = case_col.query(query_embeddings=query_vector, n_results=3)

    formatted_context = "=== CONSTITUTIONAL LAW ===\n"
    for i, doc in enumerate(const_results["documents"][0]):
        article = const_results["metadatas"][0][i].get('article', 'Unknown Article')
        formatted_context += f"Source: {article}\nText: {doc}\n\n"
        
    formatted_context += "=== SUPPORTING CASE LAW ===\n"
    for i, doc in enumerate(case_results["documents"][0]):
        case_name = case_results["metadatas"][0][i].get('case_name', 'Unknown Case')
        formatted_context += f"Source: {case_name}\nText: {doc}\n\n"

    return formatted_context


# FRONT-END DESIGN
# Sidebar UI
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Scale_of_justice_2.svg/1024px-Scale_of_justice_2.svg.png", width=80)
    st.title("SheriaLens")
    st.caption("AI Legal Assistant powered by the Kenyan Constitution & Precedent Case Laws.")
    st.divider()
    st.success("🟢 Database Connected")
    st.success("🟢 Models Loaded")
    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Initializing Chat History in Browser Memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to SheriaLens! How can I assist you with Kenyan law today?"}
    ]

# Render existing chat history
for msg in st.session_state.messages:
    # Skip rendering the raw context blocks 
    if msg.get("is_context"): 
        continue
    
    avatar = "⚖️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        
        # If the assistant's message has sources attached, display them in an expander
        if "sources" in msg:
            with st.expander("📚 View Retrieved Legal Sources"):
                st.markdown(f"<div class='legal-source-box'>{msg['sources'].replace('===', '**').replace('Source:', '<br><b>Source:</b>')}</div>", unsafe_allow_html=True)


# User Interaction
if prompt := st.chat_input("Ask a legal question... (e.g., 'What are the elements of a fair trial?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Loading animation
    with st.chat_message("assistant", avatar="⚖️"):
        with st.status("Analyzing Legal Databases...", expanded=True) as status:
            st.write("Formulating legal search terms")
            search_terms = rewrite_query(prompt, st.session_state.messages)
            time.sleep(0.5) # Ensuring UI smoothness
            
            st.write(f"🔎 Scanning Constitution & Case Laws for: *'{search_terms}'*")
            legal_context = retrieve_context(search_terms)
            time.sleep(0.5)
            
            st.write("🧠 Synthesizing final legal argument...")
            
            # Prepare memory for Gemini 
            gemini_history = []
            for m in st.session_state.messages:
                if m.get("is_context"): continue # Don't send old heavy contexts
                role = "model" if m["role"] == "assistant" else "user"
                gemini_history.append({"role": role, "parts": [m["content"]]})
                
            # Temporarily attach the heavy context to the current question
            gemini_history[-1]["parts"] = [f"Context:\n{legal_context}\n\nQuestion: {prompt}"]
            
            # Generate Answer
            response = synthesizer.generate_content(gemini_history)
            final_answer = response.text
            
            status.update(label="Analysis Complete", state="complete", expanded=False)
        
        # The final answer and sources
        st.markdown(final_answer)
        with st.expander("📚 View Retrieved Legal Sources"):
            st.markdown(f"<div class='legal-source-box'>{legal_context.replace('===', '**').replace('Source:', '<br><b>Source:</b>')}</div>", unsafe_allow_html=True)

    # Saving the AI's response and sources to browser memory
    st.session_state.messages.append({
        "role": "assistant", 
        "content": final_answer,
        "sources": legal_context
    })