# **SheriaLens: Clarity in a world of Fine Print**

Glance of the chatbot:
              [Sherialens](https://huggingface.co/spaces/BC-254/SheriaLens2)
**Note:** Due to financial constraints, we are currently using the gemini free api hence we have api rate limits. The rate limit allows for only 5 questions in every minute(5 questions/60 seconds). Incase you pass this limit kindly be patient, it represents after 5 minutes. Thank you.

For a non-rate limited version of the same, kindly run [this notebook](Notebooks/kyalo.ipynb) notebook inside the notebooks folder.
___________________________________________

## **Overview**
The law is the code that governs our lives, yet it is written in a language few can compile. For decades, access to legal understanding has been gated behind expensive billable hours and impenetrable jargon. The gap between the "letter of the law" and the people it serves has never been wider. SheriaLens exists to bridge that gap.


*Our Mission* <br>
      
    To ensure that "Ignorance of the law is no defense" is no longer a trap, but a solvable data problem.

## **Business Understanding**
In the current legal landscape, a profound Information Asymmetry exists. On one side, there is the "Black Box" of legal statutes, precedents, and procedural nuances—accessible only to those with significant financial resources or specialized training. On the other side is the general public and small enterprises, often navigating critical life events or business decisions in the dark.

**The Problem?** <br>
The High Cost of Clarity.
Legal counsel is traditionally modeled as a luxury service, characterized by:

 * High Prohibitive Costs: High billable hours make consultation inaccessible for routine inquiries.

 * Cognitive Overload: "Legalese" is a barrier to entry. Complex syntax and archaic vocabulary alienate the very people the law is meant to protect.

 * Inefficiency: For legal professionals, hours are wasted on repetitive research and drafting that could be automated.

**The Solution:** <br>
SheriaLens as a Force Multiplier. It is not designed to replace the lawyer, but to scale legal intelligence. By leveraging Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG), we convert the static, unstructured data of law libraries into a dynamic, conversational interface.

We are thus building the "First Mile" of Legal Defense:

 * For Individuals: Instant interpretation of rights including but not limited to rental agreements and traffic laws.

 * For SMEs: Automated compliance checks and contract summarization, reducing overhead.

 * For Legal Pros: A high-speed research assistant that retrieves specific case law and statutes in seconds, not hours.

**Market Positioning:** <br>
We operate at the intersection of LegalTech and Generative AI. Unlike traditional legal databases (which are just search engines for lawyers), SheriaLens focuses on Synthesis and Accessibility.

*Our Value Proposition:*

    To reduce the marginal cost of legal understanding to zero.


## **Data Understanding**
The foundation of SheriaLens is built upon a massive, unstructured corpus of legal documentation. 

1. **The Primary Sources** 

Our ingestion pipeline focuses on the authoritative pillars of the judicial system:

 * *The Constitution*: The supreme law of the land, serving as the root node for all legal reasoning.

 * *The Acts of Parliament & Statutes*: The codified rules governing specific domains (e.g., The Penal Code, The Employment Act, The Traffic Act). These documents provide the "hard rules" for our model's logic.

 * *Case Laws & Precedents*: Thousands of court rulings and judgments. This data provides the "interpretive layer" showing how static laws are applied in dynamic, real-world scenarios.

<br>

2. **Data Acquisition & Quality** <br>

The data was sourced from public legal repositories (e.g., National Council for Law Reporting/Kenya Law Reports). The raw format consists largely of:

 * Unstructured Text Blocks: Long-form paragraphs requiring extensive segmentation.

 * PDF/Scanned Documents: Necessitating Optical Character Recognition (OCR) pipelines to convert visual archives into machine-readable text.

## **Data Preparation**

Legal documents are notoriously dense and unstructured. To prepare this data for a machine learning pipeline, we implemented the following preprocessing strategy:

* **Text Extraction & Cleaning:** We utilized text extraction libraries(e.g., PyPDF2 and pdfplumber) to pull text from raw PDFs of the Kenyan Constitution and various court case laws. We then cleaned the text by removing boilerplate headers, footers, and non-informative watermarks.
* **Semantic Chunking:** Because legal contexts are highly nuanced, standard character-split chunking often breaks the logical flow of a statute. We applied semantic chunking to ensure that clauses, subsections, and related legal arguments remain intact within the same text block.
* **Embedding Generation:** The cleaned and chunked text was converted into dense vector representations using pre-trained embedding models. This process maps the semantic meaning of the legal text into a high-dimensional vector space, enabling similarity searches.

## **Modeling & System Architecture**

SheriaLens is a Retrieval-Augmented Generation (RAG) architecture that ensures highly accurate, context-aware responses hence mitigating LLM hallucinations.

**1. The Retrieval Pipeline**
* **Vector Database:** We index our document embeddings into a vector store. When a user queries the system (e.g., "What are my rights as a tenant?"), the query is embedded into the same vector space.
* **Context Search:** The system performs a similarity search to retrieve the top *k* most relevant legal chunks—drawing directly from the ingested statutes and case laws.

**2. The Generative Pipeline**
* **Large Language Model (LLM):** We utilize the Gemini API as our generative engine.
* **Prompt Engineering:** The retrieved legal chunks are injected into a carefully engineered prompt alongside the user's original query. The LLM is instructed to act as a legal assistant, synthesizing **only** the provided context to formulate a plain-English, easily digestible answer.

## **Evaluation**

Our evaluation strategy focuses on the reliability and safety of the RAG pipeline:

* **Context Precision:** Does the retriever pull the correct statutes and case laws relevant to the query?
* **Answer Faithfulness (Hallucination Rate):** Does the generated response rely strictly on the retrieved legal context, or does it invent legal precedent? We strictly optimize for high faithfulness to ensure users receive factual interpretations.
* **Readability:** Assessing whether the output successfully translates complex legalese into accessible language for the ordinary mwananchi without losing the core legal meaning.

## **Deployment & Future Roadmap**

SheriaLens is currently deployed as an interactive web application hosted on HuggingFace Spaces. The user interface is designed for simplicity, allowing users to converse with the legal corpus seamlessly.

**Next Steps:**
* **Expanding the Knowledge Base:** Integrating a wider array of domain-specific laws (e.g., comprehensive tax laws, family law, and corporate compliance).
* **User Authentication & History:** Allowing users to save queries and track ongoing legal research.
* **Enterprise API Integration:** Developing a B2B solution for law firms and SMEs to plug SheriaLens directly into their internal compliance and research workflows as we scale this initiative into a fully-fledged legal-tech startup.
