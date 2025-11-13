# Backend

Backend FastAPI para um chatbot com IA que fornece respostas fundamentadas sobre o vestibular Unicamp 2026.

## Stack

- [**Python**](https://www.python.org/) - Linguagem de programação
  - [**uv**](https://github.com/astral-sh/uv) - Gerenciador de pacotes Python rápido
  - [**Ruff**](https://docs.astral.sh/ruff/) - Lint e formatação
  - [**Makefile**](https://www.gnu.org/software/make/) - Comandos de desenvolvimento
- [**FastAPI**](https://fastapi.tiangolo.com/) - Framework web moderno e rápido
- [**Pydantic**](https://docs.pydantic.dev/latest/) - Validação de dados
  - [**Pydantic Settings**](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Configurações de variáveis de ambiente
- [**SQLModel**](https://sqlmodel.tiangolo.com/) - ORM SQL para Python
  - [**PostgreSQL**](https://www.postgresql.org/) - Banco de dados
  - [**Psycopg2**](https://www.psycopg.org/docs/) - Driver PostgreSQL para Python
- [**Alembic**](https://alembic.sqlalchemy.org/en/latest/) - Ferramenta de migração de banco de dados
- [**OpenAI Python SDK**](https://platform.openai.com/docs/api-reference/introduction?lang=python) - SDK para acessar as APIs da OpenAI e outras provedores de IA compatíveis
- [**Authlib**](https://docs.authlib.org/en/latest/) - Autenticação
   - [**GitHub OAuth Application**](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) - Provedor de autenticação fácil e não-burocrático
- [**Docker**](https://www.docker.com/) & [**Docker Compose**](https://docs.docker.com/compose/) - Conteinerização

Se você não estiver familiarizado com as diferentes tecnologias usadas neste projeto, consulte a documentação correspondente de cada uma.

## Pré-requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) gerenciador de pacotes
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (para ambiente conteinerizado)

## Início Rápido

1. **Instale as dependências:**
     ```bash
     make install
     ```

2. **Configure o ambiente:**
    
     Copie o arquivo `.env.example` para `.env`, rodando:
   
      ```bash
      make setup-env
      ```

     Em seguida, preencha os valores. Leia o conteúdo do arquivo para mais informações.


3. **Suba o container Docker do banco de dados:**
     ```bash
     make up
     ```

4. **Aplique as migrações do banco de dados:**
     ```bash
     make db-migrate
     ```

5. **Inicie o servidor de desenvolvimento:**
     ```bash
     make dev
     ```

A API estará disponível em `http://localhost:8000` com documentação interativa em `http://localhost:8000/docs`.

## Estrutura de Pastas

```
backend/
├── app/
|   ├── .vscode/          # Configurações do VS Code
│   ├── config/           # Configurações da aplicação
│   │   ├── ai.py         # Configuração de IA (OpenAI, tools)
│   │   ├── auth.py       # Configuração de autenticação
│   │   ├── db.py         # Configuração do banco de dados
│   │   └── settings.py   # Configurações de variáveis de ambiente
│   ├── models/           # Modelos SQLModel (ORM)
│   │   ├── ai.py         # Modelos relacionados a IA (chat, mensagens, etc.)
│   │   └── auth.py       # Modelos de autenticação (user)
│   ├── repositories/     # Camada de acesso a dados
│   │   ├── ai.py         # Operações relacionadas a IA (chat, mensagens, etc.)
│   │   └── auth.py       # Operações de autenticação
│   ├── routers/          # Manipuladores de rotas da API
│   │   ├── auth.py       # Endpoints de autenticação
│   │   ├── chat.py       # Endpoints de chat
│   │   └── health.py     # Endpoints de health check
│   ├── schemas/          # Schemas Pydantic (validação)
│   │   ├── ai.py         # Schemas relacionados a IA (chat, mensagens, etc.)
│   │   └── auth.py       # Schemas de autenticação
│   ├── utils/            # Funções utilitárias
│   │   ├── auth.py       # Utilitários de autenticação (JWT, cookies, etc.)
│   │   └── ai.py         # Utilitários relacionados a IA (conversão de mensagens, streaming de respostas, etc.)
│   └── main.py           # Ponto de entrada da aplicação
├── migrations/           # Arquivos de migração do Alembic
│   ├── versions/         # Arquivos de versão das migrações
│   ├── env.py            # Configuração do ambiente Alembic
│   └── script.py.mako    # Template de migração
├── tests/                # Arquivos de teste
├── alembic.ini           # Configuração do Alembic
├── docker-compose.yml    # Serviços Docker
└── Dockerfile            # Definição do container
```

## Documentação

O FastAPI já gera automaticamente a documentação OpenAPI para esta API. Você pode acessar a interface interativa em `http://localhost:8000/docs`. Isso ajuda a entender a API, testar os endpoints e realizar chamadas à API.

Os principais comandos de desenvolvimento estão no arquivo `Makefile` e podem ser rodados usando `make <comando>`. Para ver a lista completa, basta executar `make help`.

Caso queira mais detalhes sobre alguma tecnologia utilizada, consulte a documentação oficial correspondente.
