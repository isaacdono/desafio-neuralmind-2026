import os
import logging

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- 1. Configuração de Caminhos ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(SCRIPT_DIR, "..", "..", "storage")
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data")
PDF_PATH = os.path.join(DATA_DIR, "edital_unicamp.pdf")

# --- 2. Configuração do Modelo de Embedding (Cohere) ---
if not os.getenv("COHERE_API_KEY"):
    logger.error("COHERE_API_KEY não encontrada no .env!")

embeddings = CohereEmbeddings(
    model="embed-v4.0", # ou embed-multilingual-v3.0
    cohere_api_key=os.getenv("COHERE_API_KEY")
)

# --- 3. Carregamento Imediato (Eager Loading) ---

try:
    # Verifica se o índice FAISS já existe na pasta storage
    # O FAISS salva arquivos como index.faiss e index.pkl
    if not os.path.exists(os.path.join(PERSIST_DIR, "index.faiss")):
        logger.info("Índice FAISS não encontrado. Criando novo...")
        
        # 1. Carregar o PDF
        if os.path.exists(PDF_PATH):
            logger.info(f"Carregando PDF: {PDF_PATH}")
            loader = PyPDFLoader(PDF_PATH)
            raw_documents = loader.load()
        else:
            logger.warning(f"PDF não encontrado em {PDF_PATH}. Criando índice vazio.")
            raw_documents = []

        if raw_documents:
            # 2. Quebrar o texto (Chunking)
            # O LangChain precisa disso explícito, diferente do LlamaIndex
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            documents = text_splitter.split_documents(raw_documents)
            logger.info(f"Documento dividido em {len(documents)} pedaços (chunks).")

            # 3. Criar Vetores e Indexar (FAISS)
            vectorstore = FAISS.from_documents(documents, embeddings)
            
            # 4. Salvar no disco
            os.makedirs(PERSIST_DIR, exist_ok=True)
            vectorstore.save_local(PERSIST_DIR)
            logger.info(f"Índice salvo em: {PERSIST_DIR}")
        else:
            # Cria índice vazio para não quebrar
            vectorstore = FAISS.from_texts([" "], embeddings)
            
    else:
        logger.info("Carregando índice FAISS existente do disco...")
        # allow_dangerous_deserialization é necessário para carregar arquivos pickle locais confiáveis
        vectorstore = FAISS.load_local(
            PERSIST_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )

    # Cria o "retriever" (o objeto de busca) com Rerank
    # 1. Base Retriever: "Rede de Pesca Larga"
    # Aumentamos k para garantir que o chunk relevante seja capturado.
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

    # 2. Compressor: "O Filtro Inteligente"
    # A Cohere reordena os 20 e pega apenas os top_n mais relevantes.
    compressor = CohereRerank(
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        model="rerank-multilingual-v3.0", # Modelo mais recente e multilíngue
        top_n=4 
    )

    # 3. Pipeline Final
    retriever_instance = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )

except Exception as e:
    logger.error(f"Falha crítica ao inicializar RAG com LangChain: {e}", exc_info=True)
    retriever_instance = None


# --- 4. A Ferramenta ---
def search_edital(query: str) -> str:
    """
    Busca no edital da Unicamp usando o retriever RAG configurado.
    """
    logger.info(f"Executando busca RAG para a query: '{query}'")
    try:
        # CORREÇÃO: O método padrão para executar um retriever é 'invoke'
        nodes = retriever_instance.invoke(query)
        
        if not nodes:
            logger.warning(f"Nenhum documento relevante encontrado para a query: '{query}'")
            return "Nenhuma informação encontrada no edital para esta pergunta."

        # Formata o contexto com metadados da página
        context_list = []
        for node in nodes:
            # PyPDFLoader do LangChain usa a chave 'page' (0-indexed)
            page_number = node.metadata.get("page", "N/A")
            # Converte para número de página real (1-indexed) se for um número
            if isinstance(page_number, int):
                page_number += 1
            
            text = node.page_content.replace("\n", " ")
            context_list.append(f"[Fonte: Página {page_number}] {text}")

        context_str = "\n\n---\n\n".join(context_list)
        logger.info(f"Contexto encontrado para a query '{query}':\n{context_str[:500]}...")
        return context_str
    
    except Exception as e:
        logger.error(f"Erro durante a busca RAG para a query '{query}': {e}", exc_info=True)
        return "Ocorreu um erro ao tentar buscar a informação no edital."


# print(search_edital("Quais são os requisitos para inscrição?"))  # Teste rápido