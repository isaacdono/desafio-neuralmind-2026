import os

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core.retrievers import BaseRetriever

from dotenv import load_dotenv
load_dotenv()

# Constrói caminhos absolutos a partir da localização do arquivo
# __file__ é backend/app/services/rag.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho para backend/storage
PERSIST_DIR = os.path.join(SCRIPT_DIR, "..", "..", "storage")
# Caminho para backend/data
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data")

# Configura o modelo de embedding do Cohere globalmente para o LlamaIndex
Settings.embed_model = CohereEmbedding(
    model_name="embed-v4.0",
    api_key=os.getenv("COHERE_API_KEY")
)
Settings.embed_batch_size = 10

if not os.path.exists(PERSIST_DIR):
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

retriever: BaseRetriever = index.as_retriever(similarity_top_k=3)

def search_edital(query: str) -> str:
    """
    Ferramenta RAG: Apenas busca os trechos de texto relevantes no edital.
    """
    # Apenas busca os nós (trechos)
    nodes = retriever.retrieve(query)
    
    # Concatena o texto dos trechos em uma string de contexto
    context_str = "\n\n---\n\n".join([n.get_content() for n in nodes])
    
    if not context_str:
        return "Nenhuma informação relevante encontrada no edital para essa consulta."
        
    return context_str
