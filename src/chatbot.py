import os
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv


class SheriaLensAssistant:
    def __init__(self, db_path="./sherialens_db"):
        print("Loading SheriaLens Infrastructure...")
        
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API Key not found!")
        genai.configure(api_key=api_key)

        # Initializing the Models
        self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        self.llm_model = genai.GenerativeModel('gemini-2.5-flash')
        self.synthesizer_model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="""You are SheriaLens, an expert legal AI assistant. 
            Answer the user's question using ONLY the provided legal context. 
            Ground your answer in Constitutional Law first, then use Supporting Case Law. 
            Always cite the specific Article or Case Name provided in the context.
            If the context does not contain the answer, say 'I cannot find this in the database.'"""
        )

        # Initializing chromadb
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.constitution_collection = self.chroma_client.get_collection("constitution")
        self.caselaws_collection = self.chroma_client.get_collection("caselaws")

        # Initializing Memory
        self.chat_history = []

    def rewrite_query(self, user_query):
        """Rewrites the query using BOTH the new question and previous chat history."""
        # Convert history into a readable string for the rewriter
        history_text = "\n".join([f"{msg['role']}: {msg['parts'][0]}" for msg in self.chat_history[-6:]]) 
        
        prompt = f"""
        You are an expert legal researcher. Look at the recent conversation history and the new user question.
        Determine exactly what the user is asking for right now, resolving any pronouns (like "it" or "they").
        Extract the core legal concepts and keywords to create a highly effective database search query. 
        Do not answer the question, just output the search terms.
        
        Recent Conversation:
        {history_text if history_text else "None (First interaction)"}
        
        New User Question: {user_query}
        Search Terms:
        """
        
        response = self.llm_model.generate_content(prompt)
        optimized_query = response.text.strip()
        print(f"\n[System: Rewrote Search -> '{optimized_query}']")
        return optimized_query

    def content_retrieval(self, optimized_query, top_k_const=2, top_k_cases=3):
        """Searches DB and adds citations into the context."""
        query_vector = self.embedding_model.encode([optimized_query]).tolist()
        const_results = self.constitution_collection.query(query_embeddings=query_vector, n_results=top_k_const)
        case_results = self.caselaws_collection.query(query_embeddings=query_vector, n_results=top_k_cases)

        formatted_context = "=== CONSTITUTIONAL LAW ===\n"
        for i, doc in enumerate(const_results["documents"][0]):
            # Getting the article number if it exists
            meta = const_results["metadatas"][0][i]
            article = meta.get('article', 'Unknown Article')
            formatted_context += f"- [Source: {article}]: {doc}\n\n"
            
        formatted_context += "=== SUPPORTING CASE LAW ===\n"
        for i, doc in enumerate(case_results["documents"][0]):
            # Safely grab the case name if it exists
            meta = case_results["metadatas"][0][i]
            case_name = meta.get('case_name', 'Unknown Case')
            formatted_context += f"- [Source: {case_name}]: {doc}\n\n"
        return formatted_context

    def generate_response(self, user_query):
        search_terms = self.rewrite_query(user_query)
        legal_context = self.content_retrieval(search_terms)
        temporary_prompt = f"Here is the database context:\n{legal_context}\n\nUser Question: {user_query}"
        messages_to_send = self.chat_history + [{"role": "user", "parts": [temporary_prompt]}]
        
        # Generating the final answer
        try:
            response = self.synthesizer_model.generate_content(messages_to_send)
            final_answer = response.text
            
            # Updating the history
            self.chat_history.append({"role": "user", "parts": [user_query]})
            self.chat_history.append({"role": "model", "parts": [final_answer]})
            return final_answer
            
        except Exception as e:
            return f"An error occurred while communicating with Gemini: {e}"


# The Entry Point
if __name__ == "__main__":
    assistant = SheriaLensAssistant()
    print("SheriaLens Assistant Initialized. Type 'exit' to quit.")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Closing SheriaLens. Goodbye!")
            break
            
        if not user_input.strip():
            continue
            
        answer = assistant.generate_response(user_input)
        
        print(f"\nSheriaLens: {answer}\n")
        