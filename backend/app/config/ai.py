from typing import Annotated

from fastapi import Depends
from openai import OpenAI

from app.config.settings import SettingsDep
from app.services.rag import search_edital


def get_openai_client(settings: SettingsDep):
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )


OpenAIClientDep = Annotated[OpenAI, Depends(get_openai_client)]

# Tool examples: https://github.com/vercel-labs/ai-sdk-preview-python-streaming/blob/main/api/utils/tools.py
TOOL_DEFINITIONS = [
    {
        "name": "search_edital",
        "description": "Busca trechos relevantes do Edital Unicamp 2026. Recebe {\"query\": \"texto de busca\"}.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Pergunta ou termo a buscar no edital"}
            },
            "required": ["query"],
        },
    }
]

AVAILABLE_TOOLS = {
    "search_edital": search_edital
}