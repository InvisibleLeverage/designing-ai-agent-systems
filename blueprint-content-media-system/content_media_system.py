"""
AI Content & Media System — Blueprint 7

Full content pipeline with Topic Intelligence feedback loop.
Content strategy compounds with volume: engagement data → topic scores → better briefs.

Differentiator from Blueprint 3: this system learns which topics and angles perform best
and uses that data to inform the next editorial brief.

Production swap-ins:
  - TopicIntelligenceStore → PostgreSQL + pgvector
  - EngagementCollector   → GA4 / Chartbeat API (nightly batch)
  - CMS publisher         → WordPress / Webflow / Ghost REST API
"""
import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))

OPUS   = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"

DIVERSITY_CAP   = 0.30   # no topic > 30% of monthly output
MAX_TOPIC_SLOTS = 5      # how many top topics to recommend


# ── Topic Intelligence Store (stub → PostgreSQL + pgvector in production) ─────

@dataclass
class TopicScore:
    topic:           str
    angle:           str
    score:           float = 0.0
    publish_count:   int   = 0
    last_updated:    float = field(default_factory=time.time)


class TopicIntelligenceStore:
    """In-memory stub. Replace with PostgreSQL + pgvector for production."""
    def __init__(self):
        self._scores: dict[str, TopicScore] = {}   # key = f"{topic}::{angle}"

    def update_score(self, topic: str, angle: str, engagement: dict) -> float:
        """
        Engagement score formula:
          clicks×1 + shares×3 + replies×2 + saves×4
        Weight quality signals (saves, replies) more than vanity metrics (clicks).
        """
        score = (
            engagement.get("clicks",  0) * 1 +
            engagement.get("shares",  0) * 3 +
            engagement.get("replies", 0) * 2 +
            engagement.get("saves",   0) * 4
        )
        key = f"{topic}::{angle}"
        if key in self._scores:
            existing = self._scores[key]
            # Exponential moving average — recent data weighted more
            score = existing.score * 0.7 + score * 0.3
            self._scores[key] = TopicScore(
                topic=topic, angle=angle, score=score,
                publish_count=existing.publish_count + 1,
            )
        else:
            self._scores[key] = TopicScore(topic=topic, angle=angle, score=score, publish_count=1)
        return score

    def get_recommendations(self, exclude_dominant: Optional[str] = None) -> list[TopicScore]:
        """Return top topics by score, applying diversity constraint."""
        all_scores = sorted(self._scores.values(), key=lambda s: s.score, reverse=True)
        total      = sum(s.publish_count for s in all_scores) or 1
        return [
            s for s in all_scores
            if not (exclude_dominant and s.topic == exclude_dominant and
                    s.publish_count / total > DIVERSITY_CAP)
        ][:MAX_TOPIC_SLOTS]

    def top_angle_for_topic(self, topic: str) -> Optional[str]:
        candidates = [s for s in self._scores.values() if s.topic == topic]
        return max(candidates, key=lambda s: s.score).angle if candidates else None


# ── Engagement Collector (stub → GA4 / Chartbeat API in production) ──────────

@dataclass
class PublishedContent:
    content_id: str
    topic:      str
    angle:      str
    title:      str
    published_at: float = field(default_factory=time.time)


class EngagementCollector:
    """Stub. Replace with GA4/Chartbeat API for nightly batch ingestion."""
    def collect(self, content_id: str) -> dict:
        """Returns engagement metrics. Production: fetch from analytics API."""
        import random; random.seed(hash(content_id) % 1000)
        return {
            "clicks":  random.randint(200,  2000),
            "shares":  random.randint(10,   200),
            "replies": random.randint(5,    80),
            "saves":   random.randint(20,   400),
        }


# ── Content Pipeline (same core as Blueprint 3, fed by Topic Intelligence) ───

def _call(model: str, system: str, user: str, max_tokens: int) -> str:
    r = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return r.content[0].text.strip()


def research_topic(topic: str, angle: str, audience: str) -> str:
    return _call(SONNET,
        system="You are a content researcher. Find key facts and angles. Flag unverifiable claims.",
        user=f"Research topic: {topic}\nAngle: {angle}\nAudience: {audience}\n\n"
             f"Provide: 3–4 supporting facts, examples, and data points. Flag unverifiable claims.",
        max_tokens=600)


def build_outline(topic: str, angle: str, research: str) -> list[str]:
    text = _call(SONNET,
        system="You are a content architect. Build outlines for engagement.",
        user=f"Topic: {topic}\nAngle: {angle}\nResearch:\n{research[:500]}\n\n"
             f"Output 4–5 section headings. One per line starting with ##.",
        max_tokens=250)
    return [l.strip() for l in text.split("\n") if l.strip().startswith("##")]


def write_section(heading: str, topic: str, research: str, brand_voice: str) -> str:
    return _call(OPUS,
        system=f"Content writer. Voice: {brand_voice}. 200–300 words per section. No filler.",
        user=f"Section: {heading}\nTopic: {topic}\nContext:\n{research[:400]}\n\n"
             f"Write the section. One concrete example. End with a transition.",
        max_tokens=600)


async def write_all_sections(outline: list[str], topic: str, research: str, brand_voice: str) -> list[str]:
    loop = asyncio.get_event_loop()
    return list(await asyncio.gather(*[
        loop.run_in_executor(None, write_section, h, topic, research, brand_voice)
        for h in outline
    ]))


def edit_article(draft: str, brand_voice: str) -> str:
    return _call(SONNET,
        system=f"Senior editor. Voice: {brand_voice}. Return complete edited article.",
        user=f"Edit for voice consistency and flow:\n\n{draft}\n\nFix transitions and tone. Keep all facts.",
        max_tokens=3000)


async def adapt_channels(article: str, topic: str) -> dict:
    loop = asyncio.get_event_loop()
    def linkedin():
        return _call(HAIKU, system="LinkedIn writer.",
            user=f"LinkedIn post from:\n\n{article[:1500]}\n\nHook → 3 insights → question → hashtags. 800–1200 chars.",
            max_tokens=400)
    def twitter():
        return _call(HAIKU, system="Twitter/X thread writer.",
            user=f"8-tweet thread from:\n\n{article[:1500]}\n\nTweet 1: hook. 2–7: insights (n/8). 8: CTA. ≤280 chars each.",
            max_tokens=500)
    def email():
        return _call(HAIKU, system="Email subject line writer.",
            user=f"5 subject lines for: {topic}\n\n{article[:300]}\n\nVary styles. ≤55 chars each. One per line.",
            max_tokens=120)
    def newsletter():
        return _call(HAIKU, system="Newsletter editor.",
            user=f"Newsletter brief (150–200 words) from:\n\n{article[:1500]}\n\nSubheading + key insight + one takeaway.",
            max_tokens=300)

    linkedin_out, twitter_out, email_out, newsletter_out = await asyncio.gather(
        loop.run_in_executor(None, linkedin),
        loop.run_in_executor(None, twitter),
        loop.run_in_executor(None, email),
        loop.run_in_executor(None, newsletter),
    )
    return {"linkedin": linkedin_out, "twitter": twitter_out,
            "email_subjects": email_out, "newsletter": newsletter_out}


@dataclass
class ContentPackage:
    content_id:       str
    topic:            str
    angle:            str
    primary_article:  str
    channels:         dict
    word_count:       int
    review_required:  bool = True


async def run_content_pipeline(
    topic:       str,
    angle:       str,
    audience:    str,
    brand_voice: str = "authoritative, practical, jargon-free",
) -> ContentPackage:
    import uuid
    content_id = str(uuid.uuid4())[:8]

    research = research_topic(topic, angle, audience)
    outline  = build_outline(topic, angle, research)
    sections = await write_all_sections(outline, topic, research, brand_voice)

    draft    = f"# {topic}\n\n" + "\n\n".join(
        f"{h}\n\n{b}" for h, b in zip(outline, sections)
    )
    article  = edit_article(draft, brand_voice)
    channels = await adapt_channels(article, topic)

    return ContentPackage(
        content_id=content_id, topic=topic, angle=angle,
        primary_article=article, channels=channels,
        word_count=len(article.split()),
    )


# ── Weekly feedback loop ──────────────────────────────────────────────────────

def run_weekly_feedback_update(
    published_items: list[PublishedContent],
    store:           TopicIntelligenceStore,
    collector:       EngagementCollector,
) -> dict:
    """
    Collect engagement for all published content and update Topic Intelligence scores.
    Run weekly (cron job or scheduled task). Returns a summary of score updates.
    """
    updates = []
    for item in published_items:
        engagement = collector.collect(item.content_id)
        new_score  = store.update_score(item.topic, item.angle, engagement)
        updates.append({
            "content_id": item.content_id,
            "topic":      item.topic,
            "angle":      item.angle,
            "score":      round(new_score, 1),
            "engagement": engagement,
        })
    return {"updated": len(updates), "items": updates}


def get_editorial_recommendations(store: TopicIntelligenceStore) -> list[dict]:
    """Return data-driven topic + angle recommendations for the next editorial cycle."""
    recs = store.get_recommendations()
    return [
        {"topic": s.topic, "angle": s.angle, "score": round(s.score, 1),
         "published": s.publish_count}
        for s in recs
    ]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store     = TopicIntelligenceStore()
    collector = EngagementCollector()

    # Seed some prior performance data
    seed_data = [
        ("AI agent reliability", "failure modes at boundaries", "post-001"),
        ("AI agent reliability", "production vs prototype gap",  "post-002"),
        ("LLM cost management",  "token budget engineering",     "post-003"),
        ("Multi-agent systems",  "orchestration failure modes",  "post-004"),
    ]
    published = []
    for topic, angle, cid in seed_data:
        engagement = collector.collect(cid)
        store.update_score(topic, angle, engagement)
        published.append(PublishedContent(content_id=cid, topic=topic, angle=angle, title=f"{topic}: {angle}"))

    # Weekly feedback update
    update_result = run_weekly_feedback_update(published, store, collector)
    print(f"Feedback update: {update_result['updated']} items processed\n")

    # Get recommendations
    recs = get_editorial_recommendations(store)
    print("Editorial recommendations for next cycle:")
    for r in recs:
        print(f"  [{r['score']:5.1f}] {r['topic']} — {r['angle']}  ({r['published']} published)")

    # Run pipeline for top recommendation
    if recs:
        top = recs[0]
        print(f"\nGenerating content: {top['topic']} / {top['angle']}")
        pkg = asyncio.run(run_content_pipeline(
            topic=top["topic"], angle=top["angle"],
            audience="Engineering leaders building AI systems",
        ))
        print(f"\nContent ID:  {pkg.content_id}")
        print(f"Word count:  {pkg.word_count}")
        print(f"Review required: {pkg.review_required}")
        print(f"\nArticle (first 400 chars):\n{pkg.primary_article[:400]}...")
        print(f"\nLinkedIn (first 200 chars):\n{pkg.channels['linkedin'][:200]}...")
