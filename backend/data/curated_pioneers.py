"""Hand-curated bios of people widely credited with founding or advancing the
field of modern AI. There's no feed for "who matters" — this is inherently an
editorial judgment call, so it's a static list rather than something scraped
or inferred, in the same spirit as curated_models.py.

Order here is the default display order (see `sort_order` on the Pioneer
model) — roughly chronological/foundational first, then current lab leaders.
"""

CURATED_PIONEERS: list[dict] = [
    {
        "slug": "geoffrey-hinton",
        "name": "Geoffrey Hinton",
        "role": "Deep learning pioneer",
        "company_name": "University of Toronto (formerly Google)",
        "contribution": "Co-invented backpropagation and deep belief networks; the 2012 AlexNet breakthrough by his students kicked off the deep learning era.",
        "bio": "Known as one of the 'Godfathers of AI', Hinton won the 2018 Turing Award for his work on neural networks. He left Google in 2023 to speak more freely about AI safety risks.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Geoffrey_Hinton"}],
    },
    {
        "slug": "yann-lecun",
        "name": "Yann LeCun",
        "role": "Chief AI Scientist",
        "company_name": "Meta",
        "contribution": "Pioneered convolutional neural networks (CNNs), foundational to modern computer vision.",
        "bio": "A 2018 Turing Award co-recipient, LeCun leads Meta's AI research (FAIR) and is a prominent voice for open-source, open-weight models.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Yann_LeCun"}],
    },
    {
        "slug": "yoshua-bengio",
        "name": "Yoshua Bengio",
        "role": "Founder & Scientific Director",
        "company_name": "Mila (Quebec AI Institute)",
        "contribution": "Advanced neural network research on sequence modeling and attention mechanisms that underpin today's transformers.",
        "bio": "The third 2018 Turing Award co-recipient; now a leading voice on AI safety and existential-risk research.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Yoshua_Bengio"}],
    },
    {
        "slug": "ilya-sutskever",
        "name": "Ilya Sutskever",
        "role": "Co-founder",
        "company_name": "Safe Superintelligence Inc. (formerly OpenAI)",
        "contribution": "Co-authored the AlexNet paper and was OpenAI's chief scientist through GPT-3 and GPT-4, shaping the scaling-laws approach to LLMs.",
        "bio": "Left OpenAI in 2024 to found Safe Superintelligence Inc., focused solely on safely building superintelligent AI.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Ilya_Sutskever"}],
    },
    {
        "slug": "andrej-karpathy",
        "name": "Andrej Karpathy",
        "role": "Founder",
        "company_name": "Eureka Labs (formerly OpenAI, Tesla AI)",
        "contribution": "Built much of Tesla's Autopilot vision stack and was a founding member of OpenAI; widely known for making deep learning education accessible.",
        "bio": "Now building Eureka Labs, an AI-native education startup, and continues to publish influential technical explainers on LLMs.",
        "links": [{"label": "Website", "url": "https://karpathy.ai/"}],
    },
    {
        "slug": "sam-altman",
        "name": "Sam Altman",
        "role": "CEO",
        "company_name": "OpenAI",
        "contribution": "Led OpenAI through the release of ChatGPT and the GPT model series, driving the current wave of mainstream AI adoption.",
        "bio": "Former president of Y Combinator; became one of the most prominent public figures in AI following ChatGPT's 2022 launch.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Sam_Altman"}],
    },
    {
        "slug": "dario-amodei",
        "name": "Dario Amodei",
        "role": "Co-founder & CEO",
        "company_name": "Anthropic",
        "contribution": "Co-led GPT-2/GPT-3 development at OpenAI, then co-founded Anthropic to focus on AI safety research and the Claude model family.",
        "bio": "A leading voice on AI safety and interpretability, and one of several former OpenAI leaders who founded Anthropic in 2021.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Dario_Amodei"}],
    },
    {
        "slug": "demis-hassabis",
        "name": "Demis Hassabis",
        "role": "Co-founder & CEO",
        "company_name": "Google DeepMind",
        "contribution": "Co-founded DeepMind, whose AlphaGo and AlphaFold systems produced landmark AI breakthroughs in games and protein folding.",
        "bio": "Shared the 2024 Nobel Prize in Chemistry for AlphaFold's impact on protein structure prediction.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Demis_Hassabis"}],
    },
    {
        "slug": "andrew-ng",
        "name": "Andrew Ng",
        "role": "Founder",
        "company_name": "DeepLearning.AI / Landing AI",
        "contribution": "Co-founded Google Brain and Coursera; his online courses trained millions of engineers now working across the AI industry.",
        "bio": "One of the most influential AI educators globally, and a longtime advocate for practical, applied machine learning.",
        "links": [{"label": "Website", "url": "https://www.andrewng.org/"}],
    },
    {
        "slug": "fei-fei-li",
        "name": "Fei-Fei Li",
        "role": "Co-Director, Stanford HAI",
        "company_name": "Stanford University / World Labs",
        "contribution": "Created ImageNet, the large-scale labeled dataset that catalyzed the deep learning revolution in computer vision.",
        "bio": "Known as the 'Godmother of AI'; now also building World Labs, focused on spatial intelligence.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Fei-Fei_Li"}],
    },
    {
        "slug": "jensen-huang",
        "name": "Jensen Huang",
        "role": "Co-founder & CEO",
        "company_name": "Nvidia",
        "contribution": "Built Nvidia's GPUs and CUDA software stack into the computational backbone that makes modern deep learning training possible.",
        "bio": "Under Huang, Nvidia became the dominant supplier of AI training/inference hardware and one of the world's most valuable companies.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Jensen_Huang"}],
    },
    {
        "slug": "mustafa-suleyman",
        "name": "Mustafa Suleyman",
        "role": "CEO, Microsoft AI",
        "company_name": "Microsoft",
        "contribution": "Co-founded DeepMind, then Inflection AI, before leading Microsoft's consumer AI efforts (Copilot).",
        "bio": "A prominent commentator on AI policy and the long-term societal impact of increasingly capable AI systems.",
        "links": [{"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Mustafa_Suleyman"}],
    },
]
