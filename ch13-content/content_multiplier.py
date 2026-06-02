"""
Content Multiplier — Chapter 13: AI Content and Media Systems

One primary piece → N platform-native derivatives.
Brand voice is injected into every generation prompt.

Formats:
  twitter_thread     — hook + 7 insights + CTA, ≤280 chars per tweet
  linkedin_post      — hook → context → insight → closing question
  newsletter_section — subheading → context → insight + example
  youtube_script     — hook (0–30 s) → sections → outro + CTA
  email_subjects     — 10 A/B-testable subject line variants (JSON array)
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
REASONING_MODEL = "claude-sonnet-4-6"
FAST_MODEL      = "claude-haiku-4-5-20251001"   # email subjects only


@dataclass
class ContentVariants:
    twitter_thread:     str
    linkedin_post:      str
    newsletter_section: str
    youtube_script:     str
    email_subjects:     list[str]
    topic:              str


class ContentMultiplier:
    def __init__(self, brand_voice: str = "authoritative, practical, jargon-free"):
        self.brand_voice = brand_voice

    # ── Public API ───────────────────────────────────────────────────────────

    def generate_all(self, source_content: str, topic: str) -> ContentVariants:
        """
        Generate all format variants concurrently.
        Returns a ContentVariants dataclass with one field per platform.
        """
        generators = {
            "twitter":    lambda: self._twitter_thread(source_content, topic),
            "linkedin":   lambda: self._linkedin_post(source_content, topic),
            "newsletter": lambda: self._newsletter_section(source_content, topic),
            "youtube":    lambda: self._youtube_script(source_content, topic),
            "email":      lambda: self._email_subjects(source_content, topic),
        }

        results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(fn): key for key, fn in generators.items()}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as exc:
                    results[key] = f"[generation failed: {exc}]"

        subjects = []
        try:
            raw = results.get("email", "[]")
            if "```" in raw:
                raw = raw.split("```")[1].lstrip("json").strip()
            data = json.loads(raw)
            subjects = data if isinstance(data, list) else data.get("subjects", [])
        except (json.JSONDecodeError, KeyError):
            subjects = [results.get("email", "")]

        return ContentVariants(
            twitter_thread=results.get("twitter", ""),
            linkedin_post=results.get("linkedin", ""),
            newsletter_section=results.get("newsletter", ""),
            youtube_script=results.get("youtube", ""),
            email_subjects=subjects,
            topic=topic,
        )

    # ── Format generators ─────────────────────────────────────────────────────

    def _twitter_thread(self, content: str, topic: str) -> str:
        return self._generate(
            model=REASONING_MODEL,
            instruction=(
                f"Write a Twitter/X thread about: {topic}\n"
                f"Voice: {self.brand_voice}\n\n"
                f"FORMAT — exactly this structure:\n"
                f"Tweet 1: Hook (strong claim or surprising insight, ≤280 chars)\n"
                f"Tweet 2–8: One insight per tweet, numbered (2/8), ≤280 chars each\n"
                f"Tweet 9: CTA — ask a question or invite a reply\n\n"
                f"Source material:\n{content[:3000]}"
            ),
        )

    def _linkedin_post(self, content: str, topic: str) -> str:
        return self._generate(
            model=REASONING_MODEL,
            instruction=(
                f"Write a LinkedIn post about: {topic}\n"
                f"Voice: {self.brand_voice}\n\n"
                f"FORMAT:\n"
                f"- Opening hook (1–2 sentences, no preamble)\n"
                f"- Context or problem (2–3 sentences)\n"
                f"- Core insight (3–5 sentences, the main value)\n"
                f"- Closing question to drive comments\n"
                f"- 3–5 relevant hashtags\n"
                f"- Total: 800–1200 characters\n\n"
                f"Source material:\n{content[:3000]}"
            ),
        )

    def _newsletter_section(self, content: str, topic: str) -> str:
        return self._generate(
            model=REASONING_MODEL,
            instruction=(
                f"Write a newsletter section about: {topic}\n"
                f"Voice: {self.brand_voice}\n\n"
                f"FORMAT:\n"
                f"- Bold subheading (≤8 words)\n"
                f"- Opening context (2–3 sentences)\n"
                f"- Core insight with a concrete example\n"
                f"- One actionable takeaway\n"
                f"- Total: 600–1000 words\n\n"
                f"Source material:\n{content[:3000]}"
            ),
        )

    def _youtube_script(self, content: str, topic: str) -> str:
        return self._generate(
            model=REASONING_MODEL,
            instruction=(
                f"Write a YouTube video script about: {topic}\n"
                f"Voice: {self.brand_voice}\n\n"
                f"FORMAT:\n"
                f"[HOOK — 0–30s]: Open with a question, stat, or claim that creates "
                f"urgency. Do not introduce yourself yet.\n"
                f"[INTRO — 30–60s]: Who this is for and what they will learn.\n"
                f"[SECTION 1–3]: Main content, one concept per section with examples.\n"
                f"[OUTRO]: Summary of key points + CTA (subscribe / comment / resource).\n"
                f"- Mark each section with [SECTION NAME]\n"
                f"- Total: 800–1500 words\n\n"
                f"Source material:\n{content[:3000]}"
            ),
        )

    def _email_subjects(self, content: str, topic: str) -> str:
        return self._generate(
            model=FAST_MODEL,
            instruction=(
                f"Generate 10 email subject lines for content about: {topic}\n"
                f"Voice: {self.brand_voice}\n\n"
                f"Requirements: varied styles (question, number, how-to, curiosity gap, "
                f"direct benefit). Each ≤60 characters.\n\n"
                f'Respond ONLY with valid JSON: {{"subjects": ["...", "..."]}}\n\n'
                f"Source material:\n{content[:1500]}"
            ),
        )

    # ── Shared generator ──────────────────────────────────────────────────────

    def _generate(self, model: str, instruction: str) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": instruction}],
        )
        return response.content[0].text.strip()


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    source = """
    AI agent systems fail at boundaries, not at the centre.
    The handoff between agents, the edge of a context window, the transition from
    tool call to reasoning — these are where production failures concentrate.
    Engineers who design for boundary failures build systems that survive production.
    Those who optimise reasoning quality alone encounter failures they cannot diagnose.
    The architectural insight: every reliability investment should target boundaries first.
    """

    multiplier = ContentMultiplier(brand_voice="technical, direct, no hype")
    variants   = multiplier.generate_all(source, "Why AI agents fail at boundaries")

    print("=== TWITTER THREAD ===")
    print(variants.twitter_thread[:400], "...\n")

    print("=== LINKEDIN POST (first 300 chars) ===")
    print(variants.linkedin_post[:300], "...\n")

    print("=== EMAIL SUBJECTS ===")
    for i, subj in enumerate(variants.email_subjects[:5], 1):
        print(f"  {i}. {subj}")
