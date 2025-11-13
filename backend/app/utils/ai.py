import json
import logging
import traceback
import uuid
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from sqlmodel import Session

from app.config.db import engine
from app.repositories.ai import save_chat
from app.schemas.ai import ClientMessage


# # Adiciona uma configuração básica de logging para ver a saída no console
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Você é um assistente especialista no edital do Vestibular Unicamp 2026.
Sua missão é responder perguntas sobre o vestibular.

REGRAS ESTABELECIDAS:
1.  Para perguntas sobre o vestibular, use a ferramenta `search_edital`.
2.  Se não encontrar a resposta, devolva: "Não encontrei essa informação específica no edital."
3.  Procure ser direto ao ponto.
"""


def convert_to_openai_messages(
    messages: List[ClientMessage],
) -> List[ChatCompletionMessageParam]:
    openai_messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for message in messages:
        message_parts: List[dict] = []
        tool_calls = []
        tool_result_messages = []

        if message.parts:
            for part in message.parts:
                if part.type == "text":
                    # Ensure empty strings default to ''
                    message_parts.append({"type": "text", "text": part.text or ""})

                elif part.type == "file":
                    if (
                        part.contentType
                        and part.contentType.startswith("image")
                        and part.url
                    ):
                        message_parts.append(
                            {"type": "image_url", "image_url": {"url": part.url}}
                        )
                    elif part.url:
                        # Fall back to including the URL as text if we cannot map the file directly.
                        message_parts.append({"type": "text", "text": part.url})

                elif part.type.startswith("tool-"):
                    tool_call_id = part.toolCallId
                    tool_name = part.toolName or part.type.replace("tool-", "", 1)

                    if tool_call_id and tool_name:
                        should_emit_tool_call = False

                        if part.state and any(
                            keyword in part.state for keyword in ("call", "input")
                        ):
                            should_emit_tool_call = True

                        if part.input is not None or part.args is not None:
                            should_emit_tool_call = True

                        if should_emit_tool_call:
                            arguments = (
                                part.input if part.input is not None else part.args
                            )
                            if isinstance(arguments, str):
                                serialized_arguments = arguments
                            else:
                                serialized_arguments = json.dumps(arguments or {})

                            tool_calls.append(
                                {
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": serialized_arguments,
                                    },
                                }
                            )

                        if part.state == "output-available" and part.output is not None:
                            tool_result_messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "content": json.dumps(part.output),
                                }
                            )

        elif message.content is not None:
            message_parts.append({"type": "text", "text": message.content})

        if not message.parts and message.experimental_attachments:
            for attachment in message.experimental_attachments:
                if attachment.contentType.startswith("image"):
                    message_parts.append(
                        {"type": "image_url", "image_url": {"url": attachment.url}}
                    )

                elif attachment.contentType.startswith("text"):
                    message_parts.append({"type": "text", "text": attachment.url})

        if message.toolInvocations:
            for toolInvocation in message.toolInvocations:
                tool_calls.append(
                    {
                        "id": toolInvocation.toolCallId,
                        "type": "function",
                        "function": {
                            "name": toolInvocation.toolName,
                            "arguments": json.dumps(toolInvocation.args),
                        },
                    }
                )

        if message_parts:
            if len(message_parts) == 1 and message_parts[0]["type"] == "text":
                content_payload = message_parts[0]["text"]
            else:
                content_payload = message_parts
        else:
            # Ensure that we always provide some content for OpenAI
            content_payload = ""

        openai_message: ChatCompletionMessageParam = {
            "role": message.role,  # type: ignore
            "content": content_payload,
        }

        if tool_calls:
            openai_message["tool_calls"] = tool_calls  # type: ignore

        openai_messages.append(openai_message)

        if message.toolInvocations:
            for toolInvocation in message.toolInvocations:
                tool_message = {
                    "role": "tool",
                    "tool_call_id": toolInvocation.toolCallId,
                    "content": json.dumps(toolInvocation.result),
                }

                openai_messages.append(tool_message)  # type: ignore

        openai_messages.extend(tool_result_messages)  # type: ignore

    return openai_messages


def stream_text(
    client: OpenAI,
    messages: Sequence[ChatCompletionMessageParam],
    tool_definitions: Sequence[Dict[str, Any]],
    available_tools: Mapping[str, Callable[..., Any]],
    model: str,
    protocol: str = "data",
):
    """Yield Server-Sent Events for a streaming chat completion."""
    try:
        # logger.info("--- Chamada para API OpenAI (1ª) ---")
        # logger.info(f"MODEL: {model}")
        # logger.info(f"MESSAGES: {json.dumps(list(messages), indent=2, ensure_ascii=False)}")
        # logger.info("------------------------------------")

        def format_sse(payload: dict) -> str:
            return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"

        message_id = f"msg-{uuid.uuid4().hex}"
        text_stream_id = "text-1"
        text_started = False
        text_finished = False
        finish_reason = None
        usage_data = None
        tool_calls_state: Dict[int, Dict[str, Any]] = {}

        yield format_sse({"type": "start", "messageId": message_id})

        stream = client.chat.completions.create(
            messages=messages,
            model=model,
            stream=True,
            tools=tool_definitions,
        )

        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason

                delta = choice.delta
                if delta is None:
                    continue

                if delta.content is not None:
                    if not text_started:
                        yield format_sse({"type": "text-start", "id": text_stream_id})
                        text_started = True
                    yield format_sse(
                        {
                            "type": "text-delta",
                            "id": text_stream_id,
                            "delta": delta.content,
                        }
                    )

                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        state = tool_calls_state.setdefault(
                            index,
                            {
                                "id": None,
                                "name": None,
                                "arguments": "",
                                "started": False,
                            },
                        )

                        if tool_call_delta.id is not None:
                            state["id"] = tool_call_delta.id
                            if (
                                state["id"] is not None
                                and state["name"] is not None
                                and not state["started"]
                            ):
                                yield format_sse(
                                    {
                                        "type": "tool-input-start",
                                        "toolCallId": state["id"],
                                        "toolName": state["name"],
                                    }
                                )
                                state["started"] = True

                        function_call = getattr(tool_call_delta, "function", None)
                        if function_call is not None:
                            if function_call.name is not None:
                                state["name"] = function_call.name
                                if (
                                    state["id"] is not None
                                    and state["name"] is not None
                                    and not state["started"]
                                ):
                                    yield format_sse(
                                        {
                                            "type": "tool-input-start",
                                            "toolCallId": state["id"],
                                            "toolName": state["name"],
                                        }
                                    )
                                    state["started"] = True

                            if function_call.arguments:
                                if (
                                    state["id"] is not None
                                    and state["name"] is not None
                                    and not state["started"]
                                ):
                                    yield format_sse(
                                        {
                                            "type": "tool-input-start",
                                            "toolCallId": state["id"],
                                            "toolName": state["name"],
                                        }
                                    )
                                    state["started"] = True

                                state["arguments"] += function_call.arguments
                                if state["id"] is not None:
                                    yield format_sse(
                                        {
                                            "type": "tool-input-delta",
                                            "toolCallId": state["id"],
                                            "inputTextDelta": function_call.arguments,
                                        }
                                    )

            if not chunk.choices and chunk.usage is not None:
                usage_data = chunk.usage

        if finish_reason == "stop" and text_started and not text_finished:
            yield format_sse({"type": "text-end", "id": text_stream_id})
            text_finished = True

        if finish_reason == "tool_calls":
            # Append the assistant's tool-calling message
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": state["id"],
                        "type": "function",
                        "function": {"name": state["name"], "arguments": state["arguments"]},
                    }
                    for state in tool_calls_state.values()
                ],
            }
            messages = list(messages)  # Convert sequence to list to append
            messages.append(assistant_message)

            # Execute tools and gather results
            for index in sorted(tool_calls_state.keys()):
                state = tool_calls_state[index]
                tool_call_id = state.get("id")
                tool_name = state.get("name")
                raw_arguments = state["arguments"]

                try:
                    parsed_arguments = json.loads(raw_arguments) if raw_arguments else {}
                    tool_function = available_tools.get(tool_name)
                    
                    if tool_function:
                        tool_result = tool_function(**parsed_arguments)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(tool_result),
                            }
                        )
                    else:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps({"error": f"Tool '{tool_name}' not found."}),
                            }
                        )

                except Exception as e:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps({"error": str(e)}),
                        }
                    )

            # # Second call to OpenAI with tool results
            # logger.info("--- Chamada para API OpenAI (2ª, com resultado da tool) ---")
            # logger.info(f"MODEL: {model}")
            # logger.info(f"MESSAGES: {json.dumps(list(messages), indent=2, ensure_ascii=False)}")
            # logger.info("----------------------------------------------------------")
            second_stream = client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
                tools=tool_definitions,
            )

            for chunk in second_stream:
                for choice in chunk.choices:
                    if choice.finish_reason is not None:
                        finish_reason = choice.finish_reason

                    delta = choice.delta
                    if delta is None:
                        continue

                    if delta.content is not None:
                        if not text_started:
                            yield format_sse({"type": "text-start", "id": text_stream_id})
                            text_started = True
                        yield format_sse(
                            {
                                "type": "text-delta",
                                "id": text_stream_id,
                                "delta": delta.content,
                            }
                        )
                
                if not chunk.choices and chunk.usage is not None:
                    usage_data = chunk.usage


        if text_started and not text_finished:
            yield format_sse({"type": "text-end", "id": text_stream_id})
            text_finished = True

        finish_metadata: Dict[str, Any] = {}
        if finish_reason is not None:
            finish_metadata["finishReason"] = finish_reason.replace("_", "-")

        if usage_data is not None:
            usage_payload = {
                "promptTokens": usage_data.prompt_tokens,
                "completionTokens": usage_data.completion_tokens,
            }
            total_tokens = getattr(usage_data, "total_tokens", None)
            if total_tokens is not None:
                usage_payload["totalTokens"] = total_tokens
            finish_metadata["usage"] = usage_payload

        if finish_metadata:
            yield format_sse({"type": "finish", "messageMetadata": finish_metadata})
        else:
            yield format_sse({"type": "finish"})

        yield "data: [DONE]\n\n"
    except Exception as e:
        traceback.print_exc()
        # Send error message in SSE format instead of raising
        error_message = str(e)

        yield format_sse(
            {
                "type": "error",
                "errorText": error_message,
            }
        )
        yield "data: [DONE]\n\n"


def stream_text_with_persistence(
    client: OpenAI,
    messages: Sequence[ChatCompletionMessageParam],
    tool_definitions: Sequence[Dict[str, Any]],
    available_tools: Mapping[str, Callable[..., Any]],
    model: str,
    protocol: str,
    ui_messages: List[dict[str, Any]],
    chat_id: str,
    user_id: int,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Stream text response with persistence support.
    Tracks message completion and saves to database when stream completes.
    """
    collected_delta: List[str] = []
    message_id: Optional[str] = None

    for event in stream_text(
        client,
        messages,
        tool_definitions,
        available_tools,
        model,
        protocol,
    ):
        # Parse SSE event to track message completion
        if isinstance(event, str) and event.startswith("data: "):
            try:
                data_str = event[6:].strip()
                if data_str == "[DONE]":
                    # Save messages when stream completes
                    assistant_msg = {
                        "id": message_id or f"msg-{uuid.uuid4().hex[:16]}",
                        "role": "assistant",
                        "parts": [{"type": "text", "text": "".join(collected_delta)}],
                    }
                    final_messages = ui_messages + [assistant_msg]

                    # Create a wrapper that creates a new session for the background task
                    def save_chat_task():
                        try:
                            with Session(engine) as bg_session:
                                save_chat(bg_session, chat_id, user_id, final_messages)
                        except Exception as e:
                            # Log error but don't fail the request
                            logger = logging.getLogger(__name__)
                            logger.error(
                                f"Failed to save chat {chat_id}: {e}",
                                exc_info=True,
                            )

                    background_tasks.add_task(save_chat_task)
                else:
                    data = json.loads(data_str)
                    if data.get("type") == "start":
                        message_id = data.get("messageId")
                    elif data.get("type") == "text-delta":
                        delta = data.get("delta", "")
                        collected_delta.append(delta)
            except Exception:
                pass

        yield event


def patch_response_with_headers(
    response: StreamingResponse,
    protocol: str = "data",
) -> StreamingResponse:
    """Apply the standard streaming headers expected by the Vercel AI SDK."""

    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    if protocol:
        response.headers.setdefault("x-vercel-ai-protocol", protocol)

    return response
