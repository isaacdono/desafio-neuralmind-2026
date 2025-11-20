# Workspace: Desafio Estágio Verão 2026 da NeuralMind

Esse repositório se estrutura em uma VS Code Workspace desenvolvida para realizar o Desafio Estágio Verão 2026 da NeuralMind. Recomendamos que você utilize uma workspace unificada para facilitar a navegação entre as pastas e o desenvolvimento do projeto, especialmente considerando que você atuará em dois ambientes distintos: Python e Node.js.

Caso você não esteja familiarizado com o VS Code Workspace, consulte a documentação oficial: [VS Code Workspace](https://code.visualstudio.com/docs/editor/workspaces).

## Sobre Este Projeto

**Nota Importante:** Este projeto veio pré-pronto como base para o desafio. A implementação principal desenvolvida foi um **sistema RAG (Retrieval-Augmented Generation)** no arquivo [`backend/app/services/rag.py`](./backend/app/services/rag.py).

### Implementação do Sistema RAG

O sistema RAG foi desenvolvido para permitir consultas inteligentes ao edital da Unicamp, utilizando técnicas avançadas de recuperação de informação e inteligência artificial. A implementação inclui:

#### Componentes Principais:

1. **Carregamento de Documentos**
   - Utiliza `PyPDFLoader` do LangChain para processar o edital em formato PDF
   - Extrai o conteúdo do documento `edital_unicamp.pdf`

2. **Chunking (Divisão de Texto)**
   - Implementa `RecursiveCharacterTextSplitter` para dividir o documento em pedaços menores
   - Configuração: chunks de 800 caracteres com overlap de 200 caracteres
   - Separadores hierárquicos: `\n\n`, `\n`, espaço e caracteres vazios

3. **Embeddings e Vetorização**
   - Utiliza **Cohere Embeddings** (modelo `embed-v4.0`)
   - Converte texto em vetores numéricos para busca semântica

4. **Armazenamento Vetorial**
   - Implementa **FAISS** (Facebook AI Similarity Search) para indexação e busca eficiente
   - Persiste o índice em disco (pasta `storage/`) para reutilização
   - Carregamento lazy: cria índice apenas se não existir

5. **Busca e Reranking**
   - **Base Retriever**: busca inicial recuperando os 20 chunks mais similares (k=20)
   - **Cohere Rerank**: utiliza modelo `rerank-multilingual-v3.0` para reordenar resultados
   - **ContextualCompressionRetriever**: pipeline que combina busca ampla + reranking inteligente
   - Retorna os 4 chunks mais relevantes (top_n=4) após o rerank

6. **Função de Busca**
   - `search_edital(query: str)`: função principal que executa consultas no edital
   - Retorna contexto formatado com referências às páginas do documento original
   - Tratamento de erros e logging detalhado

#### Tecnologias Utilizadas:
- **LangChain**: framework principal para RAG
- **Cohere API**: embeddings e reranking
- **FAISS**: banco de dados vetorial
- **Python dotenv**: gerenciamento de variáveis de ambiente

Este sistema permite que usuários façam perguntas em linguagem natural sobre o edital e recebam respostas precisas com referências às páginas originais do documento.

## Pré-requisitos

- [VS Code](https://code.visualstudio.com/) ou algum editor de código compatível com VS Code, como [Cursor](https://www.cursor.com/).

**Nota:** Cada pasta possui um arquivo `README.md` detalhando seus pré-requisitos e instruções específicas para execução e desenvolvimento naquele módulo. Você também precisará instalar as extensões recomendadas para cada pasta. Verifique o arquivo `.vscode/extensions.json` dentro de cada pasta para mais informações.

## Início Rápido

1. Clone o repositório:
   ```bash
   git clone https://github.com/neuralmind-ai/desafio-nm-estagio-de-verao-2026.git
   ```
2. Abra a pasta no VS Code.
3. Abra a paleta de comandos (Ctrl+Shift+P ou Cmd+Shift+P).
4. Procure por "File: Open Workspace from File..." e execute-o.
5. Selecione o arquivo `project.code-workspace`.
6. O workspace será aberto.

Em seguida, você pode abrir o terminal no VS Code e executar os comandos para instalar as dependências e iniciar o servidor de desenvolvimento de cada aplicação. Para isso, consulte o arquivo `README.md` de cada pasta.

## Estrutura de Pastas

```
desafio-nm-estagio-de-verao-2026/
├── backend/                     # Backend FastAPI
├── frontend/                    # Frontend Next.js
├── project.code-workspace       # Configuração da workspace
├── docker-compose.yml           # Orquestra todos os serviços para facilitar o desenvolvimento, deploy e/ou testes
└── README.md                    # Documentação geral do projeto (este README)
```

## Documentação

Consulte os arquivos `README.md` de cada pasta para mais informações sobre o projeto.

### Contêineres Docker

O projeto inclui um arquivo [`docker-compose.yml`](./docker-compose.yml) na raiz, que orquestra todos os serviços backend, frontend e banco de dados para facilitar o desenvolvimento e o deploy. Basta executar:

```bash
docker compose up --build
```

Isso subirá todos os serviços integrados. Caso necessário, ajuste as variáveis de ambiente nos arquivos `.env` de cada módulo ou diretamente no `docker-compose.yml` para atender aos requisitos do seu ambiente de produção ou testes.

## Capturas de Tela da Base do Projeto

![Tela de login](docs/assets/sign-in.png)
![Tela de overview](docs/assets/overview.png)
![Tela de chat](docs/assets/chatting.png)

## Contato

Para dúvidas, sugestões ou para reportar problemas, entre no nosso Slack [Desafio Estágio Verão 2026 da NeuralMind](https://join.slack.com/t/desafioneural-yqq2158/shared_invite/zt-3hfwk0rit-M~iWNDAh8HQnVqkvuCKbkw) ou entre em contato com [roberto@neuralmind.ai](mailto:roberto@neuralmind.ai) ou [luis.emidio@neuralmind.ai](mailto:luis.emidio@neuralmind.ai).

---

[Licença](LICENSE) | [Política de Segurança](SECURITY.md)
