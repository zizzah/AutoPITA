import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader   #type:ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  #type:ignore
from langchain_community.vectorstores import Chroma   #type:ignore
from langchain_huggingface import HuggingFaceEmbeddings   #type:ignore

DOCS = [
    "docs/NIGERIA-TAX-ACT-2025.pdf",
    "docs/NIGERIA-TAX-ADMINISTRATION-ACT-2025.pdf",
    "docs/Gazette - NIGERIA TAX ACT, 2025.pdf",
    "docs/Notes-on-Nigeria-s-Tax-Reform-Acts,-2025.pdf",
    "docs/the-nigeria-tax-reform-acts-top-20-changes-to-know-and-top-6-things-to-do-pwc.pdf",
    "docs/faqs_efs.pdf",
    "docs/guideline_for_efs.pdf",
    "docs/PITA-Ammendment.pdf",
]

CHROMA_DIR = "chroma_db"


def ingest():
    all_chunks = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )

    for path in DOCS:
        if not os.path.exists(path):
            print(f"SKIP (not found): {path}")
            continue

        print(f"Loading: {path}")
        try:
            loader = PyPDFLoader(path)
            pages = loader.load()
            chunks = splitter.split_documents(pages)
            all_chunks.extend(chunks)
            print(f"  → {len(pages)} pages, {len(chunks)} chunks")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Building embeddings (this takes 2-5 minutes on first run)...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    print(f"Done. Vector store saved to {CHROMA_DIR}/")
    print(f"Total vectors: {vectorstore._collection.count()}")


if __name__ == "__main__":
    ingest()