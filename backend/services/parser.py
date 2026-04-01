"""
Site parser: fetches a URL and extracts title, description, niche, keyword hints.
"""

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.models import SiteData

# Simple niche keyword map for rule-based detection
_NICHE_KEYWORDS: dict[str, list[str]] = {
    "digital-agency": [
        "реклама", "контекстная", "директ", "google ads", "таргетинг", "smm",
        "seo", "продвижение", "маркетинг", "digital", "агентство", "кампания",
        "ретаргетинг", "ppc", "контент", "брендинг", "дизайн сайта",
    ],
    "e-commerce": [
        "купить", "цена", "корзина", "магазин", "shop", "price", "buy", "cart",
        "каталог", "товар", "интернет-магазин", "доставка",
    ],
    "services": ["услуги", "сервис", "заказать", "service", "order", "booking"],
    "saas": ["платформа", "тариф", "подписка", "platform", "subscription", "pricing", "crm", "erp"],
    "real-estate": [
        "недвижимость", "квартира", "аренда", "real estate", "apartment", "rent",
        "новостройка", "ипотека", "риелтор",
    ],
    "medical": ["клиника", "врач", "лечение", "clinic", "doctor", "treatment", "медицина", "здоровье"],
    "education": ["курс", "обучение", "онлайн-школа", "course", "learning", "school", "диплом", "сертификат"],
    "finance": ["кредит", "займ", "банк", "loan", "credit", "bank", "finance", "ипотека", "инвестиции"],
}


async def parse_site(url: str) -> SiteData:
    """Fetch the page and extract key signals for niche detection."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        # Return minimal data so the pipeline can continue with manual niche input
        return SiteData(
            title=urlparse(url).netloc,
            description="",
            niche="services",
            keywords_hint=[],
        )

    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string.strip() if soup.title else urlparse(url).netloc
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    description = meta_desc_tag["content"].strip() if meta_desc_tag else ""

    # Collect visible text from headings + body sample
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    body_text = soup.get_text(" ", strip=True)[:3000].lower()
    combined = " ".join(headings).lower() + " " + body_text

    # Extract candidate keywords from headings (nouns / meaningful tokens)
    keywords_hint = _extract_hints(headings)

    niche = _detect_niche(combined)

    return SiteData(
        title=title,
        description=description,
        niche=niche,
        keywords_hint=keywords_hint[:20],
    )


def _detect_niche(text: str) -> str:
    scores: dict[str, int] = {}
    for niche, words in _NICHE_KEYWORDS.items():
        scores[niche] = sum(1 for w in words if w in text)
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "services"


_STOPWORDS = {
    # UI / навигационные слова сайтов (не должны попадать в ключи)
    "популярные", "популярный", "популярных", "категории", "категория",
    "категориях", "разделы", "раздел", "меню", "навигация", "главная",
    "страница", "сайт", "сайта", "сайте", "подробнее", "смотреть все",
    "все товары", "товары", "товар", "перейти", "нажмите", "нажать",
    "подробно", "больше", "ещё", "ещё больше", "читать далее",
    "контакты", "контакт", "телефон", "адрес", "email", "почта",
    # Предлоги и союзы
    "и", "в", "на", "с", "по", "для", "от", "до", "из", "за", "под", "над",
    "при", "о", "об", "без", "между", "через", "но", "или", "да", "же", "бы",
    "то", "что", "как", "так", "все", "это", "эта", "эти", "тот", "те", "там",
    "тут", "где", "когда", "если", "чтобы", "потому", "поэтому", "однако",
    # Местоимения и указательные
    "мы", "вы", "они", "он", "она", "оно", "я", "ты", "себя", "свой", "своя",
    "наш", "ваш", "их", "его", "ее", "нас", "вас", "нам", "вам",
    # Частицы
    "не", "ни", "бы", "же", "ли", "лишь", "уже", "ещё", "еще", "только",
    "именно", "даже", "вот", "ведь", "просто",
    # Служебные глаголы
    "быть", "есть", "было", "была", "были", "будет", "будут", "стать", "стал",
    "является", "являются", "который", "которая", "которые", "которого", "которой",
    "которым", "которых", "которому", "котором", "которую",
    # Распространённые глагольные формы из заголовков
    "создаём", "создаем", "работает", "работаем", "поможем", "помогаем",
    "делаем", "делаете", "получите", "получить", "узнать", "узнайте",
    "звоните", "пишите", "читать", "смотреть", "скачать",
    # Английские служебные
    "the", "a", "an", "of", "in", "for", "to", "and", "or", "is", "are",
    "that", "this", "with", "have", "has", "your", "our", "we", "you",
    # Общие незначимые слова
    "новый", "нова", "лучший", "лучшая", "главный", "каждый", "любой",
    "можно", "нужно", "также", "более", "очень", "самый", "всего",
}

# Verb endings that indicate non-noun words (to skip verb forms)
_VERB_ENDINGS = ("аем", "яем", "ете", "ёте", "ите", "ают", "яют",
                  "уют", "ют", "ет", "ит", "ать", "ять", "ить", "уть")

# Adjective endings — single adjective words without a noun are useless as keywords
_ADJ_ENDINGS = ("ный", "ная", "ное", "ные", "ный", "ений", "еный",
                 "ский", "ская", "ское", "ские",
                 "ный", "уемый", "уемая", "уемые",
                 "ого", "его", "ому", "ему")


def _extract_hints(headings: list[str]) -> list[str]:
    """Return unique meaningful business keyword phrases from headings."""
    tokens: list[str] = []
    seen: set[str] = set()
    bigram_words: set[str] = set()  # Words already captured inside a bigram

    for h in headings:
        # First try multi-word phrases (2-3 words) — more useful for Wordstat
        words_raw = re.split(r"[\s,.:;!?—–\-«»\"']+", h)
        words = [w.strip().lower() for w in words_raw if w.strip()]

        # Add 2-word bigrams if both words are meaningful
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i + 1]
            if (len(w1) > 3 and len(w2) > 3
                    and w1 not in _STOPWORDS and w2 not in _STOPWORDS
                    and not any(w1.endswith(e) for e in _VERB_ENDINGS)
                    and not any(w2.endswith(e) for e in _VERB_ENDINGS)):
                bigram = f"{w1} {w2}"
                if bigram not in seen:
                    tokens.append(bigram)
                    seen.add(bigram)
                    bigram_words.add(w1)
                    bigram_words.add(w2)

        # Then single meaningful nouns — skip if already part of a bigram or is an adjective
        for word in words:
            if (len(word) > 4
                    and word not in _STOPWORDS
                    and word not in seen
                    and word not in bigram_words
                    and not any(word.endswith(e) for e in _VERB_ENDINGS)
                    and not any(word.endswith(e) for e in _ADJ_ENDINGS)):
                tokens.append(word)
                seen.add(word)

    return tokens
