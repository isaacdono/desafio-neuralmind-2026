# utils/rag.py
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import CohereEmbeddings
from langchain.vectorstores import Chroma

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data")       # ajuste se necessário
PERSIST_DIR = os.path.join(SCRIPT_DIR, "..", "..", "storage") # ajuste se necessário
PDF_PATH = os.path.join(DATA_DIR, "edital_unicamp.pdf")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBED_MODEL = "embed-v4.0"

# cria/retorna um retriever (carrega ou indexa)
def _get_retriever():
    emb = CohereEmbeddings(cohere_api_key=COHERE_API_KEY, model=EMBED_MODEL)

    # se já existe chroma persistido, abre
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        db = Chroma(persist_directory=PERSIST_DIR, embedding_function=emb)
        return db.as_retriever(search_kwargs={"k": 3})

    # caso contrário: extrai com pypdf, chunka e cria índice
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF não encontrado: {PDF_PATH}")

    reader = PdfReader(PDF_PATH)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": "edital_unicamp.pdf", "page": i+1}))

    if not docs:
        raise RuntimeError("Nenhum texto extraído do PDF com pypdf.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=120)
    chunks = splitter.split_documents(docs)

    db = Chroma.from_documents(chunks, emb, persist_directory=PERSIST_DIR)
    db.persist()
    return db.as_retriever(search_kwargs={"k": 3})

# função que o ai.py chamará como tool
def search_edital(query: str) -> dict:
    """
    Recebe { "query": "..."} quando chamado via tool call.
    Retorna um dict (serializável) com os trechos relevantes.
    """
    retriever = _get_retriever()
    docs = retriever.get_relevant_documents(query)

    # monta resposta compacta e estruturada
    hits = []
    for d in docs:
        md = d.metadata or {}
        hits.append({"page": md.get("page"), "source": md.get("source"), "text": d.page_content[:200]})

    context_str = "\n\n---\n\n".join([d.page_content for d in docs])
    # retorno simples — ai.py transforma em JSON e injeta como tool result
    return {"query": query, "context": context_str, "hits": hits}
