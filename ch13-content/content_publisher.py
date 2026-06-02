"""
Content Publisher — Chapter 13: AI Content and Media Systems

Schedules content variants across platforms and renders a publishing calendar.
Pair with ContentMultiplier: generate all variants, then schedule and review.
"""
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class ScheduledPost:
    platform:     str          # "twitter" | "linkedin" | "newsletter" | "youtube" | "email"
    content:      str
    publish_date: date
    topic:        str
    status:       str = "draft"   # "draft" | "approved" | "published"
    notes:        str = ""


class ContentPublisher:
    def __init__(self):
        self._calendar: list[ScheduledPost] = []

    # ── Scheduling ────────────────────────────────────────────────────────────

    def schedule_content(
        self,
        variants:      dict,
        publish_dates: dict,
        topic:         str = "",
    ) -> list[ScheduledPost]:
        """
        Schedule content variants to publish dates.

        Args:
            variants:      dict mapping platform → content string (from ContentMultiplier)
            publish_dates: dict mapping platform → date | str (ISO 8601)
            topic:         human-readable topic label for calendar display

        Returns list of newly scheduled ScheduledPost objects.
        """
        scheduled = []
        for platform, content in variants.items():
            if platform not in publish_dates:
                continue
            raw_date = publish_dates[platform]
            pub_date = (
                datetime.strptime(raw_date, "%Y-%m-%d").date()
                if isinstance(raw_date, str)
                else raw_date
            )
            post = ScheduledPost(
                platform=platform, content=content,
                publish_date=pub_date, topic=topic,
            )
            self._calendar.append(post)
            scheduled.append(post)
        return scheduled

    def approve(self, platform: str, publish_date: date) -> int:
        """Mark matching posts as approved. Returns count updated."""
        count = 0
        for post in self._calendar:
            if post.platform == platform and post.publish_date == publish_date:
                post.status = "approved"
                count += 1
        return count

    def mark_published(self, platform: str, publish_date: date) -> int:
        count = 0
        for post in self._calendar:
            if (post.platform == platform and post.publish_date == publish_date
                    and post.status == "approved"):
                post.status = "published"
                count += 1
        return count

    # ── Calendar view ─────────────────────────────────────────────────────────

    def get_publishing_calendar(
        self,
        from_date: Optional[date] = None,
        to_date:   Optional[date] = None,
    ) -> str:
        """Render a text calendar view of scheduled posts."""
        today = date.today()
        start = from_date or today
        end   = to_date   or (today + timedelta(days=30))

        # Group by date
        by_date: dict[date, list[ScheduledPost]] = {}
        for post in self._calendar:
            if start <= post.publish_date <= end:
                by_date.setdefault(post.publish_date, []).append(post)

        if not by_date:
            return "No content scheduled in this date range."

        lines = ["PUBLISHING CALENDAR", "=" * 50]
        for d in sorted(by_date):
            lines.append(f"\n{d.strftime('%A, %d %b %Y')}")
            for post in sorted(by_date[d], key=lambda p: p.platform):
                status_icon = {"draft": "○", "approved": "●", "published": "✓"}.get(post.status, "?")
                preview = post.content[:70].replace("\n", " ")
                lines.append(f"  {status_icon} [{post.platform:12s}] {preview}…")
                if post.topic:
                    lines.append(f"             Topic: {post.topic}")
        return "\n".join(lines)

    def pending_approval(self) -> list[ScheduledPost]:
        return [p for p in self._calendar if p.status == "draft"]

    def week_summary(self, week_start: Optional[date] = None) -> dict:
        start = week_start or date.today()
        end   = start + timedelta(days=7)
        week  = [p for p in self._calendar if start <= p.publish_date < end]
        by_status: dict[str, int] = {}
        for p in week:
            by_status[p.status] = by_status.get(p.status, 0) + 1
        return {
            "week_of":        start.isoformat(),
            "total_posts":    len(week),
            "by_status":      by_status,
            "pending_review": len([p for p in week if p.status == "draft"]),
        }


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    publisher = ContentPublisher()

    today = date.today()
    variants = {
        "twitter":    "Thread: Why AI agents fail at boundaries — 9 insights\n1/9 ...",
        "linkedin":   "Most AI agent failures happen at the edges, not the centre...",
        "newsletter": "**Boundary Failures in AI Agent Systems**\nThe handoff is where...",
        "youtube":    "[HOOK] What if your AI agent fails quietly on every 10th task?...",
        "email":      json.dumps({"subjects": [
            "Why AI agents fail at boundaries (not the model)",
            "The AI reliability mistake 90% of builders make",
        ]}),
    }

    publish_dates = {
        "twitter":    today + timedelta(days=1),
        "linkedin":   today + timedelta(days=2),
        "newsletter": today + timedelta(days=3),
        "youtube":    today + timedelta(days=5),
        "email":      today + timedelta(days=3),
    }

    publisher.schedule_content(variants, publish_dates, topic="AI Agent Boundaries")
    publisher.approve("twitter", today + timedelta(days=1))

    print(publisher.get_publishing_calendar())
    print("\nWeek summary:", json.dumps(publisher.week_summary(), indent=2))
    print(f"\nPending approval: {len(publisher.pending_approval())} posts")
