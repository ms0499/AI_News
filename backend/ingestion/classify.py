"""Fast, free, rule-based tagging — runs on every article before the optional
AI pass, and is all that's needed if AI summarization is disabled."""

COMPANY_KEYWORDS = {
    "OpenAI": ["openai", "chatgpt"],
    "Anthropic": ["anthropic", "claude"],
    "Google DeepMind": ["deepmind", "google ai", "gemini"],
    "Google": ["google"],
    "Meta": ["meta ai", "meta platforms", "llama"],
    "Microsoft": ["microsoft", "copilot"],
    "Mistral": ["mistral"],
    "xAI": ["xai", "grok"],
    "Hugging Face": ["hugging face", "huggingface"],
    "Amazon": ["amazon", "aws", "bedrock"],
    "Nvidia": ["nvidia"],
    "Apple": ["apple intelligence", "apple"],
    "Cohere": ["cohere"],
    "Stability AI": ["stability ai", "stable diffusion"],
    "DeepSeek": ["deepseek"],
    "Alibaba": ["alibaba", "qwen"],
    "Moonshot AI": ["moonshot", "kimi"],
    "Perplexity": ["perplexity"],
}

MODEL_KEYWORDS = [
    "gpt-5", "gpt-4", "gpt-4o", "o3", "o1",
    "claude opus", "claude sonnet", "claude haiku",
    "gemini 3", "gemini 2.5", "gemini 2.0",
    "llama 4", "llama 3",
    "grok 4", "grok 3",
    "mistral large", "mixtral",
    "deepseek", "qwen", "kimi k2",
]

TOPIC_KEYWORDS = {
    "funding": ["funding", "raises", "series a", "series b", "series c", "valuation", "investment"],
    "release": ["release", "launches", "unveils", "announces", "rolls out"],
    "benchmark": ["benchmark", "leaderboard", "outperforms", "state-of-the-art", "sota"],
    "regulation": ["regulation", "policy", "lawsuit", "antitrust", "safety", "government"],
    "research": ["paper", "research", "arxiv", "study"],
    "acquisition": ["acquires", "acquisition", "merger"],
    "hiring": ["hires", "hiring", "departs", "resigns", "joins"],
}

SECTION_TOPIC_MAP = {
    "release": "models",
    "benchmark": "models",
    "research": "papers",
}


def classify(title: str, raw_summary: str) -> dict:
    text = f"{title} {raw_summary or ''}".lower()

    companies = [name for name, kws in COMPANY_KEYWORDS.items() if any(kw in text for kw in kws)]
    models = [m for m in MODEL_KEYWORDS if m in text]
    topics = [topic for topic, kws in TOPIC_KEYWORDS.items() if any(kw in text for kw in kws)]

    section = "news"
    for topic in topics:
        if topic in SECTION_TOPIC_MAP:
            section = SECTION_TOPIC_MAP[topic]
            break
    if section == "news" and companies:
        section = "companies"

    return {
        "companies": companies,
        "models": [m.title() for m in models],
        "topics": topics,
        "section": section,
    }
