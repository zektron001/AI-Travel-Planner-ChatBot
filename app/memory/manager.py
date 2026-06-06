from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from pypdf import PdfReader
import os
import glob


class MemoryManager:
    """Handles short-term (conversation) and long-term (FAISS vector) memory."""

    def __init__(self):
        self.short_term: dict[str, list] = {}
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = None
        self._init_vector_store()
        self._load_data_folder()

    def _init_vector_store(self):
        """Initialize FAISS vector store with a dummy doc."""
        try:
            dummy = Document(
                page_content="Travel agent initialized.", metadata={"type": "system"}
            )
            self.vector_store = FAISS.from_documents([dummy], self.embeddings)
            print("✅ Vector store initialized")
        except Exception as e:
            print(f"⚠️ Vector store init warning: {e}")
            self.vector_store = None

    def _load_data_folder(self):
        """Load all PDFs and text files from the data/ folder into FAISS."""
        data_dir = "Data"
        if not os.path.exists(data_dir):
            print("ℹ️ No data/ folder found, skipping PDF loading")
            return

        docs = []

        # ── Load PDFs ──────────────────────────────────────────────────────
        pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
        for pdf_path in pdf_files:
            try:
                reader = PdfReader(pdf_path)
                filename = os.path.basename(pdf_path)
                print(f"📄 Loading PDF: {filename} ({len(reader.pages)} pages)")
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        # Chunk into ~500 char pieces for better retrieval
                        chunks = [text[j : j + 500] for j in range(0, len(text), 500)]
                        for chunk in chunks:
                            if chunk.strip():
                                docs.append(
                                    Document(
                                        page_content=chunk,
                                        metadata={
                                            "source": filename,
                                            "page": i + 1,
                                            "type": "pdf",
                                        },
                                    )
                                )
                print(f"   ✅ Loaded {filename}")
            except Exception as e:
                print(f"   ⚠️ Could not load {pdf_path}: {e}")

        # ── Load .txt files ────────────────────────────────────────────────
        txt_files = glob.glob(os.path.join(data_dir, "*.txt"))
        for txt_path in txt_files:
            try:
                filename = os.path.basename(txt_path)
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                chunks = [text[j : j + 500] for j in range(0, len(text), 500)]
                for chunk in chunks:
                    if chunk.strip():
                        docs.append(
                            Document(
                                page_content=chunk,
                                metadata={"source": filename, "type": "txt"},
                            )
                        )
                print(f"   ✅ Loaded {filename}")
            except Exception as e:
                print(f"   ⚠️ Could not load {txt_path}: {e}")

        # ── Add all docs to FAISS ──────────────────────────────────────────
        if docs and self.vector_store:
            self.vector_store.add_documents(docs)
            print(
                f"✅ Loaded {len(docs)} chunks into vector store from {len(pdf_files + txt_files)} files"
            )
        else:
            print("ℹ️ No documents found in data/ folder")

    # ── Short-term memory ──────────────────────────────────────────────────────

    def get_history(self, session_id: str) -> list:
        return self.short_term.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.short_term:
            self.short_term[session_id] = []
        self.short_term[session_id].append({"role": role, "content": content})
        if len(self.short_term[session_id]) > 20:
            self.short_term[session_id] = self.short_term[session_id][-20:]

    def clear_session(self, session_id: str):
        self.short_term.pop(session_id, None)

    # ── Long-term memory ───────────────────────────────────────────────────────

    def save_preference(self, session_id: str, preference: str):
        if not self.vector_store:
            return
        doc = Document(
            page_content=preference,
            metadata={"session_id": session_id, "type": "preference"},
        )
        self.vector_store.add_documents([doc])

    def get_relevant_preferences(self, query: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            prefs = [
                d.page_content for d in docs if d.metadata.get("type") == "preference"
            ]
            if prefs:
                return "Remembered user preferences:\n" + "\n".join(
                    f"- {p}" for p in prefs
                )
        except Exception:
            pass
        return ""

    def search_knowledge_base(self, query: str, k: int = 4) -> str:
        """Search PDF/txt knowledge base for relevant travel info."""
        if not self.vector_store:
            return ""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            pdf_docs = [d for d in docs if d.metadata.get("type") in ("pdf", "txt")]
            if pdf_docs:
                result = "📚 From knowledge base:\n"
                for d in pdf_docs:
                    source = d.metadata.get("source", "unknown")
                    result += f"[{source}]: {d.page_content}\n\n"
                return result
        except Exception:
            pass
        return ""


# Singleton instance shared across the app
memory_manager = MemoryManager()
