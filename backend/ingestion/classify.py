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
    "Perplexity": ["perplexity ai", "perplexity.ai"],
}

# Maker for each tracked model keyword, so a release always gets attributed to
# the company that actually built it — not just whichever company an article
# happens to mention first (e.g. a "OpenAI reacts to Google's Gemini 3" story).
MODEL_MAKERS = {
    "OpenAI": ["gpt-5", "gpt-4", "gpt-4o", "o3", "o1"],
    "Anthropic": ["claude opus", "claude sonnet", "claude haiku"],
    "Google DeepMind": ["gemini 3", "gemini 2.5", "gemini 2.0"],
    "Meta": ["llama 4", "llama 3"],
    "xAI": ["grok 4", "grok 3"],
    "Mistral": ["mistral large", "mixtral"],
    "DeepSeek": ["deepseek"],
    "Alibaba": ["qwen"],
    "Moonshot AI": ["kimi k2"],
}
MODEL_TO_COMPANY = {kw: company for company, kws in MODEL_MAKERS.items() for kw in kws}
MODEL_KEYWORDS = list(MODEL_TO_COMPANY)

TOPIC_KEYWORDS = {
    "funding": ["funding", "raises", "series a", "series b", "series c", "valuation", "investment"],
    "release": ["release", "launches", "unveils", "announces", "rolls out"],
    "benchmark": ["benchmark", "leaderboard", "outperforms", "state-of-the-art", "sota"],
    "regulation": ["regulation", "policy", "lawsuit", "antitrust", "safety", "government"],
    "research": ["paper", "research", "arxiv", "study"],
    "acquisition": ["acquires", "acquisition", "merger"],
    "hiring": ["hires", "hiring", "departs", "resigns", "joins"],
}

# Priority order for turning detected topics into a section. Checked in this
# exact order (not TOPIC_KEYWORDS' order) so a research paper doesn't get
# misfiled as "models" and have the models it discusses as baselines recorded
# as fake releases. "research" (driven mostly by "arxiv") goes first because
# paper abstracts routinely contain "state-of-the-art"/"SOTA" (matching
# "benchmark") and even the bare word "release" in unrelated prose — an
# arXiv paper is a paper regardless of that incidental wording.
SECTION_PRIORITY = [
    ("research", "papers"),
    ("release", "models"),
    ("benchmark", "models"),
]


def classify(title: str, raw_summary: str) -> dict:
    text = f"{title} {raw_summary or ''}".lower()

    companies = [name for name, kws in COMPANY_KEYWORDS.items() if any(kw in text for kw in kws)]
    models = [m for m in MODEL_KEYWORDS if m in text]
    topics = [topic for topic, kws in TOPIC_KEYWORDS.items() if any(kw in text for kw in kws)]

    section = "news"
    for topic, mapped_section in SECTION_PRIORITY:
        if topic in topics:
            section = mapped_section
            break
    if section == "news" and companies:
        section = "companies"

    return {
        "companies": companies,
        "models": [m.title() for m in models],
        "topics": topics,
        "section": section,
    }
