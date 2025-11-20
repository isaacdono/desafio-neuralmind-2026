## Desafio de Engenharia de IA - Chatbot Vestibular Unicamp 2026

Este repositório é o resultado do desenvolvimento proposto pelo **Desafio Estágio Verão 2026 da NeuralMind**. O desafio consistiu em fazer um chatbot que tira dúvidas sobre o Vestibular da Unicamp 2026 com base no edital oficial, além de realizar o deploy da aplicação.

O esquema inicial contava com um chatbot funcional mas sem a utilização de RAG, o que fazia a LLM não dar respostas adequadas sobre o vestibular. A tarefa era implementar o retrieval e acrescentar a fonte da informação na resposta do chatbot, como uma forma de transparência.  

A stack do projeto implementada inicialmente é: backend FastAPI + frontend Next.js.

-----

## Contribuições Chave

Minhas contribuições com o auxílio de IA concentraram-se na implementação da lógica de IA, estabilidade do pipeline e otimização de busca.

### 1\. Implementação do Motor RAG (Backend)

O principal trabalho foi integrar uma arquitetura de busca semântica robusta ao sistema de *tool calling* existente na API.

  * **Ferramenta Desenvolvida (`backend/app/services/rag.py`):** Criei a função `search_edital` que atua como uma ferramenta (tool) para a LLM.
  * **Pipeline de Busca:** A função orquestra o RAG utilizando **LangChain** para o pipeline, **FAISS** como *Vector Store* local e **Cohere Embeddings** para vetorização.
  * **Otimização de Precisão:** Para resolver o problema de **"Lost in the Middle"** e falhas de busca em listas/tabelas, foi implementado o padrão **Wide Net + Rerank**, onde o sistema busca amplamente (`k=20`) e usa o **Cohere Rerank** para refinar e enviar apenas os 3 trechos mais precisos ao LLM (`top_n=3`).
  * **Paginação:** Modificação da função `search_edital` para contar a página em que a resposta foi encontrada e acrescentar no retorno da tool.

### 2\. Engenharia de Prompts e Ciclo de Vida do Tool

Desenvolvi a lógica necessária para garantir a comunicação de ida e volta (multi-turn) no ciclo de chamada da ferramenta (Tool Calling).

  * **Instrução do Sistema (`SYSTEM_PROMPT`):** O prompt foi configurado com regras rígidas para controlar o comportamento do LLM:
      * O LLM é instruído a **sempre** usar a ferramenta `search_edital` para perguntas sobre o vestibular.
      * O LLM é proibido de usar conhecimento prévio e deve responder apenas com base no contexto **retornado pela ferramenta**.
      * O LLM sempre cita a página em que a resposta foi encontrada como [Fonte: Página X].

-----

## Como Rodar o Projeto (Desenvolvimento Local)

A aplicação é orquestrada via Docker Compose e é a maneira mais fácil de iniciar todos os serviços (Postgres, Backend, Frontend). A última parte do desafio, que consistia em fazer o deploy da aplicação, não foi concluída.

### Pré-requisitos

  * Docker Engine e Docker Compose instalados.
  * Um arquivo `.env` preenchido na pasta `backend/` com as chaves necessárias (ex: `COHERE_API_KEY`, `JWT_SECRET`).

### Execução

1.  **Clone o Repositório**
2.  **Suba os Contêineres:**
    O `docker-compose.yml` inicia os três serviços e gerencia as dependências.
    ```bash
    docker compose up --build
    ```
3.  **Acesse a Aplicação:**
    Após o *backend* e *frontend* estarem ativos, acesse: `http://localhost:3000`
