# import logging
# from groq import AsyncGroq
# from langchain_huggingface import HuggingFaceEmbeddings #type:ignore 
# from langchain_chroma import Chroma  #type:ignore
# from app.config import get_settings

# logger = logging.getLogger(__name__)
# settings = get_settings()

# # ── Load embeddings model (same one used during ingestion) ──────────────────
# # This converts text into vectors so we can search ChromaDB
# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

# # ── Load the vector store we built with ingest_documents.py ────────────────
# # This is a local folder — no network call needed
# vectorstore = Chroma(
#     persist_directory="chroma_db",
#     embedding_function=embeddings
# )

# # ── Groq client ─────────────────────────────────────────────────────────────
# client = AsyncGroq(api_key=settings.GROQ_API_KEY)


# async def answer_tax_question(question: str) -> dict:
#     """
#     1. Embed the question into a vector
#     2. Search ChromaDB for the 4 most similar chunks
#     3. Build a prompt with those chunks as context
#     4. Ask Groq to answer using only that context
#     5. Return the answer and the sources used
#     """

#     # Step 1 & 2 — semantic search
#     # similarity_search embeds the question then finds the nearest chunks
#     docs = vectorstore.similarity_search(question, k=4)

#     if not docs:
#         return {
#             "answer": "I could not find relevant information in the tax documents.",
#             "sources": []
#         }

#     # Step 3 — build context string from retrieved chunks
#     # Each doc.page_content is one chunk of text from the PDF
#     context = "\n\n---\n\n".join([doc.page_content for doc in docs])

#     # Collect source metadata — which PDF and page each chunk came from
#     sources = [
#         {
#             "source": doc.metadata.get("source", "unknown"),
#             "page": doc.metadata.get("page", "unknown")
#         }
#         for doc in docs
#     ]

#     # Step 4 — call Groq with context + question
#     prompt = f"""You are a Nigerian tax expert assistant for AutoPITA.
# Answer the question below using ONLY the provided context from Nigerian tax law documents.
# If the answer is not clearly in the context, say: "This specific detail is not covered in the documents I have. Please consult a tax professional."
# Be specific, cite section numbers where visible, and keep the answer concise.

# Context from Nigerian Tax Act 2025:
# {context}

# Question: {question}

# Answer:"""

#     response = await client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a Nigerian tax law expert. Answer only from the provided context. Never make up tax rules."
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         temperature=0.1,
#         max_tokens=1024,
#     )

#     answer = response.choices[0].message.content

#     return {
#         "answer": answer,
#         "sources": sources
#     }






async def answer_tax_question(question: str) -> dict:
    return {
        "answer": "Tax chat is coming soon. Please consult a tax professional for now.",
        "sources": []
    }