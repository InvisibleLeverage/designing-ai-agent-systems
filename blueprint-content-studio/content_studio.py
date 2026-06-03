"""
AI Content Studio — Blueprint 3

Brief → research + SEO → parallel section drafting → edit → channel variants.
Cost: $0.40–0.80 per full content package (Opus sections, Haiku adapters).
"""
import asyncio
import os
from dataclasses import dataclass, field

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))

OPUS   = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"


@dataclass
class EditorialBrief:
    topic:        str
    audience:     str
    goal:         str            # "thought_leadership" | "seo" | "lead_gen" | "education"
    brand_voice:  str = "authoritative, practical, jargon-free"
    target_words: int = 1500


@dataclass
class ContentPackage:
    primary_article: str
    linkedin_post:   str
    twitter_thread:  str
    email_subject:   str
    meta_description: str
    word_count:      int
    sections_written: int


def _call(model: str, system: str, user: str, max_tokens: int = 1024) -> str:
    r = client.messages.create(
        model=model, max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return r.content[0].text.strip()


# ── Stage 1: Research + Keyword Strategy (parallel) ──────────────────────────

def research_topic(brief: EditorialBrief) -> str:
    return _call(
        SONNET,
        system="You are a content researcher. Find key facts, angles, and supporting evidence. Flag unverifiable claims.",
        user=(
            f"Research this topic for a {brief.goal} article:\n"
            f"Topic: {brief.topic}\nAudience: {brief.audience}\n\n"
            f"Provide: 3–4 key angles, supporting facts, examples, and data points. "
            f"Max 8 sources worth referencing. Flag any claim you cannot verify."
        ),
        max_tokens=800,
    )


def keyword_strategy(brief: EditorialBrief) -> str:
    return _call(
        HAIKU,
        system="You are an SEO strategist.",
        user=(
            f"Generate a keyword strategy for: {brief.topic}\nAudience: {brief.audience}\n\n"
            f"Provide: primary keyword, 4–5 semantic keywords, and H2/H3 heading suggestions. "
            f"Keyword density target: 1.5–2%. No keyword stuffing."
        ),
        max_tokens=300,
    )


# ── Stage 2: Outline ──────────────────────────────────────────────────────────

def build_outline(brief: EditorialBrief, research: str, keywords: str) -> list[str]:
    text = _call(
        SONNET,
        system="You are a content architect. Build outlines for engagement and SEO.",
        user=(
            f"Build a section outline for this article:\n"
            f"Topic: {brief.topic}\nGoal: {brief.goal}\nAudience: {brief.audience}\n\n"
            f"Research:\n{research[:600]}\n\nKeywords:\n{keywords[:300]}\n\n"
            f"Output 4–6 section headings. One per line, starting with ##. "
            f"Each heading should be SEO-friendly and signal value to the reader."
        ),
        max_tokens=300,
    )
    return [
        line.strip()
        for line in text.split("\n")
        if line.strip().startswith("##")
    ]


# ── Stage 3: Parallel section writing ────────────────────────────────────────

def write_section(heading: str, brief: EditorialBrief, research: str) -> str:
    return _call(
        OPUS,
        system=(
            f"You are a content writer. Voice: {brief.brand_voice}. "
            f"Write for {brief.audience}. Be specific — no filler sentences."
        ),
        user=(
            f"Write this section of a {brief.goal} article:\n"
            f"Section: {heading}\n\n"
            f"Research context:\n{research[:500]}\n\n"
            f"Requirements: 200–300 words. One concrete example or data point. "
            f"No adjectives like 'innovative' or 'cutting-edge'. "
            f"End with a transition that leads into the next section."
        ),
        max_tokens=600,
    )


async def write_all_sections(
    outline: list[str], brief: EditorialBrief, research: str
) -> list[str]:
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, write_section, heading, brief, research)
        for heading in outline
    ]
    return list(await asyncio.gather(*tasks))


# ── Stage 4: Editor ───────────────────────────────────────────────────────────

def edit_article(draft: str, brief: EditorialBrief) -> str:
    return _call(
        SONNET,
        system=(
            f"You are a senior editor. Voice: {brief.brand_voice}. "
            f"Fix flow and tone consistency. Return the full edited article — do not summarise."
        ),
        user=(
            f"Edit this article for voice consistency, flow, and quality:\n\n{draft}\n\n"
            f"Fix: tone inconsistencies between sections, awkward transitions, "
            f"repeated phrases, and any sentences that add no value. "
            f"Preserve all facts and structure. Return the complete edited article."
        ),
        max_tokens=3000,
    )


# ── Stage 5: Channel adaptation (parallel) ───────────────────────────────────

def adapt_linkedin(article: str, brief: EditorialBrief) -> str:
    return _call(
        HAIKU,
        system=f"You write LinkedIn posts. Voice: {brief.brand_voice}.",
        user=(
            f"Write a LinkedIn post from this article:\n\n{article[:1500]}\n\n"
            f"Format: hook (1 line) → 3 insights → closing question → 3 hashtags. "
            f"Total: 800–1200 characters. Native LinkedIn feel — not a link dump."
        ),
        max_tokens=400,
    )


def adapt_twitter(article: str, brief: EditorialBrief) -> str:
    return _call(
        HAIKU,
        system=f"You write Twitter/X threads. Voice: {brief.brand_voice}.",
        user=(
            f"Write an 8-tweet thread from this article:\n\n{article[:1500]}\n\n"
            f"Tweet 1: hook. Tweets 2–7: one insight each (numbered n/8). "
            f"Tweet 8: CTA. Each tweet ≤ 280 characters."
        ),
        max_tokens=500,
    )


def adapt_email_subject(article: str, brief: EditorialBrief) -> str:
    return _call(
        HAIKU,
        system="You write email subject lines.",
        user=(
            f"Write 5 email subject lines for this article:\n\n{article[:500]}\n\n"
            f"Vary styles: question, number, how-to, curiosity gap, direct. "
            f"Each ≤ 55 characters. One per line."
        ),
        max_tokens=150,
    )


def adapt_meta(article: str, brief: EditorialBrief) -> str:
    return _call(
        HAIKU,
        system="You write SEO meta descriptions.",
        user=(
            f"Write a meta description for this article:\n\n{article[:500]}\n\n"
            f"Requirements: 140–155 characters, includes primary keyword, "
            f"clear value proposition, action-oriented."
        ),
        max_tokens=80,
    )


async def adapt_all_channels(article: str, brief: EditorialBrief) -> dict[str, str]:
    loop = asyncio.get_event_loop()
    linkedin, twitter, email, meta = await asyncio.gather(
        loop.run_in_executor(None, adapt_linkedin,      article, brief),
        loop.run_in_executor(None, adapt_twitter,       article, brief),
        loop.run_in_executor(None, adapt_email_subject, article, brief),
        loop.run_in_executor(None, adapt_meta,          article, brief),
    )
    return {"linkedin": linkedin, "twitter": twitter,
            "email_subjects": email, "meta_description": meta}


# ── Full pipeline ─────────────────────────────────────────────────────────────

async def run_content_studio(brief: EditorialBrief) -> ContentPackage:
    # Stage 1: research + keywords (parallel)
    loop = asyncio.get_event_loop()
    research, keywords = await asyncio.gather(
        loop.run_in_executor(None, research_topic, brief),
        loop.run_in_executor(None, keyword_strategy, brief),
    )

    # Stage 2: outline
    outline  = build_outline(brief, research, keywords)

    # Stage 3: parallel section writing
    sections = await write_all_sections(outline, brief, research)

    # Assemble draft
    draft_parts = []
    for heading, body in zip(outline, sections):
        draft_parts.append(f"{heading}\n\n{body}")
    draft = f"# {brief.topic}\n\n" + "\n\n".join(draft_parts)

    # Stage 4: edit
    article = edit_article(draft, brief)

    # Stage 5: channel adaptation (parallel)
    channels = await adapt_all_channels(article, brief)

    return ContentPackage(
        primary_article=article,
        linkedin_post=channels["linkedin"],
        twitter_thread=channels["twitter"],
        email_subject=channels["email_subjects"],
        meta_description=channels["meta_description"],
        word_count=len(article.split()),
        sections_written=len(sections),
    )


if __name__ == "__main__":
    brief = EditorialBrief(
        topic="Why AI agents fail at production boundaries",
        audience="Engineering managers and CTOs building AI systems",
        goal="thought_leadership",
        brand_voice="technical, direct, no hype",
    )

    pkg = asyncio.run(run_content_studio(brief))

    print(f"Sections: {pkg.sections_written}  |  Words: {pkg.word_count}")
    print(f"\n=== ARTICLE (first 500 chars) ===\n{pkg.primary_article[:500]}...")
    print(f"\n=== LINKEDIN POST ===\n{pkg.linkedin_post[:300]}...")
    print(f"\n=== EMAIL SUBJECTS ===\n{pkg.email_subject}")
    print(f"\n=== META ===\n{pkg.meta_description}")
