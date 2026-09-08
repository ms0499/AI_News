"""Hand-curated reference list of flagship models per company, with a
plain-language "what it's best for" description. This exists because the
ingestion pipeline only records a model when some article happens to
mention it — most tracked companies have zero rows in `model_releases`
at any given time, and the ones that do exist often carry a raw tag dump
(from the Hugging Face source) instead of a useful description.

`CURATED_MODELS` adds net-new rows for companies ingestion hasn't covered
yet. `ENRICHED_DESCRIPTIONS` overwrites the description on an existing
row (matched by company slug + case-insensitive model name) when it's
missing or is just a HF tag dump — it never touches a row that already
has a real editorial description (e.g. OpenAI's ingested rows).
"""

CURATED_MODELS: dict[str, list[dict]] = {
    "openai": [
        {
            "model_name": "GPT-4o",
            "release_date": "2024-05-13",
            "description": "Fast, natively multimodal model (text, vision, audio) — best for everyday assistant tasks and real-time conversation.",
        },
        {
            "model_name": "o1",
            "release_date": "2024-09-12",
            "description": "OpenAI's first reasoning model, thinks step-by-step before answering — best for hard math, science, and coding problems.",
        },
    ],
    "anthropic": [
        {
            "model_name": "Claude Opus",
            "release_date": None,
            "description": "Anthropic's most capable model — best for complex reasoning, long documents, and careful multi-step coding or agentic work.",
        },
        {
            "model_name": "Claude Sonnet",
            "release_date": None,
            "description": "Balanced speed and intelligence — best for everyday coding and writing at a lower cost than Opus.",
        },
        {
            "model_name": "Claude Haiku",
            "release_date": None,
            "description": "Anthropic's fastest, cheapest model — best for high-volume, low-latency tasks like classification and simple chat.",
        },
    ],
    "google-deepmind": [
        {
            "model_name": "Gemini Flash",
            "release_date": "2024-05-14",
            "description": "Lightweight, low-latency Gemini variant — best for high-volume production apps where speed and cost matter most.",
        },
    ],
    "meta": [
        {
            "model_name": "Llama 3",
            "release_date": "2024-04-18",
            "description": "Meta's flagship open-weight model family — best for self-hosting, fine-tuning, and cost-sensitive deployments.",
        },
    ],
    "microsoft": [
        {
            "model_name": "Phi-4",
            "release_date": None,
            "description": "Microsoft's small, efficient model family — best for on-device or low-cost tasks that don't need a giant model.",
        },
    ],
    "mistral": [
        {
            "model_name": "Mistral Large",
            "release_date": None,
            "description": "Mistral's flagship API model — best for enterprise-grade reasoning and multilingual tasks.",
        },
    ],
    "deepseek": [
        {
            "model_name": "DeepSeek-R1",
            "release_date": None,
            "description": "Open-weight reasoning model — best for step-by-step problem solving at a fraction of the cost of closed models.",
        },
    ],
    "alibaba": [
        {
            "model_name": "Qwen2.5",
            "release_date": None,
            "description": "Alibaba's open-weight model family — best for multilingual chat and coding, widely used for self-hosting.",
        },
    ],
    "amazon": [
        {
            "model_name": "Amazon Nova",
            "release_date": None,
            "description": "Amazon's in-house foundation model family on Bedrock — best for AWS-native enterprise apps that need tight cost control.",
        },
    ],
    "apple": [
        {
            "model_name": "Apple Intelligence (on-device models)",
            "release_date": None,
            "description": "Apple's on-device foundation models — best for privacy-preserving tasks handled directly on iPhone/Mac without sending data to the cloud.",
        },
    ],
    "cohere": [
        {
            "model_name": "Command R+",
            "release_date": "2024-04-04",
            "description": "Cohere's retrieval-augmented generation model — best for enterprise search and RAG applications over private data.",
        },
    ],
    "moonshot-ai": [
        {
            "model_name": "Kimi",
            "release_date": None,
            "description": "Moonshot AI's long-context assistant — best for tasks that need very large context windows, like big documents or research.",
        },
    ],
    "nvidia": [
        {
            "model_name": "Nemotron",
            "release_date": None,
            "description": "Nvidia's open model family, tuned for synthetic data generation and reasoning — best for teams building custom fine-tuned models.",
        },
    ],
    "perplexity": [
        {
            "model_name": "Sonar",
            "release_date": None,
            "description": "Perplexity's search-augmented model — best for up-to-date, cited question answering.",
        },
    ],
    "stability-ai": [
        {
            "model_name": "Stable Diffusion",
            "release_date": "2022-08-22",
            "description": "Stability AI's open image-generation model — best for text-to-image generation and self-hosted creative workflows.",
        },
    ],
    "xai": [
        {
            "model_name": "Grok",
            "release_date": None,
            "description": "xAI's flagship assistant model, integrated into X (Twitter) — best for real-time information and conversational search.",
        },
    ],
}

ENRICHED_DESCRIPTIONS: dict[tuple[str, str], str] = {
    (
        "google-deepmind",
        "gemini 3",
    ): "Google's flagship multimodal model — best for reasoning across text, images, video, and very large context windows.",
    (
        "alibaba",
        "qwen",
    ): "Alibaba's open-weight model family — best for multilingual chat and coding, widely used for self-hosting.",
    (
        "deepseek",
        "deepseek",
    ): "DeepSeek's general-purpose open-weight flagship — best for coding and general chat at low inference cost.",
    (
        "mistral",
        "mixtral",
    ): "Mistral's open-weight mixture-of-experts model — best for self-hosted deployments that want strong quality at lower compute cost.",
}
