"""
Чат с маркетинговым ассистентом по отчёту.

Ответы строятся только по переданным данным отчёта (контекст в промпте) — без выдумок.
Провайдер: тот же, что в ai_summary (anthropic / openai / xai).
"""

import json
from backend.services.ai_summary import _get_provider
from backend.config import settings

SYSTEM = """Ты — PPC-маркетолог, ассистент по отчёту. Отвечай только на основе приведённых ниже данных отчёта.
Если в данных нет ответа на вопрос — так и скажи: «В отчёте этого нет».
Не придумывай цифры и факты. Формат: коротко и по делу, можно списком."""


async def chat_with_report(report_json: dict, question: str) -> str:
    provider = _get_provider()
    context = json.dumps(report_json, ensure_ascii=False, indent=0)[:25000]

    if provider == "anthropic" and settings.anthropic_api_key:
        return await _chat_claude(context, question)
    if provider == "openai" and settings.openai_api_key:
        return await _chat_openai(context, question)
    if provider == "xai" and settings.xai_api_key:
        return await _chat_xai(context, question)
    if settings.anthropic_api_key:
        return await _chat_claude(context, question)
    if settings.openai_api_key:
        return await _chat_openai(context, question)
    if settings.xai_api_key:
        return await _chat_xai(context, question)

    return "Добавьте в .env один из ключей: ANTHROPIC_API_KEY, OPENAI_API_KEY или XAI_API_KEY — чтобы включить нейросеть-ассистента."


async def _chat_claude(context: str, question: str) -> str:
    import anthropic
    from backend.services.token_counter import counter
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = "claude-sonnet-4-20250514"
    user_content = f"Данные отчёта:\n{context}\n\nВопрос пользователя: {question}"
    message = await client.messages.create(
        model=model,
        max_tokens=800,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    counter.record(model, message.usage.input_tokens, message.usage.output_tokens)
    return (message.content[0].text or "").strip()


async def _chat_openai(context: str, question: str) -> str:
    from openai import AsyncOpenAI
    from backend.services.token_counter import counter
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    model = "gpt-4o-mini"
    user_content = f"Данные отчёта:\n{context}\n\nВопрос пользователя: {question}"
    r = await client.chat.completions.create(
        model=model,
        max_tokens=800,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_content},
        ],
    )
    if r.usage:
        counter.record(model, r.usage.prompt_tokens, r.usage.completion_tokens)
    return (r.choices[0].message.content or "").strip()


async def _chat_xai(context: str, question: str) -> str:
    from openai import AsyncOpenAI
    from backend.services.token_counter import counter
    client = AsyncOpenAI(api_key=settings.xai_api_key, base_url="https://api.x.ai/v1")
    model = "grok-3-mini"
    user_content = f"Данные отчёта:\n{context}\n\nВопрос пользователя: {question}"
    r = await client.chat.completions.create(
        model=model,
        max_tokens=800,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_content},
        ],
    )
    if r.usage:
        counter.record(model, r.usage.prompt_tokens, r.usage.completion_tokens)
    return (r.choices[0].message.content or "").strip()
