"""
CRM Intelligence System — Chapter 14: AI Business Automation Systems

Analyses interaction patterns, surfaces follow-up opportunities, drafts outreach.
Uses SQLite for the contact and interaction store — swap for Postgres / HubSpot in production.
"""
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    company       TEXT,
    email         TEXT,
    created_at    TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS interactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id    TEXT NOT NULL REFERENCES contacts(id),
    type          TEXT NOT NULL,   -- 'email' | 'call' | 'meeting' | 'demo'
    summary       TEXT,
    occurred_at   TEXT NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id    TEXT NOT NULL REFERENCES contacts(id),
    title         TEXT NOT NULL,
    value_usd     REAL DEFAULT 0,
    stage         TEXT DEFAULT 'prospect',  -- 'prospect' | 'qualified' | 'proposal' | 'closed'
    created_at    TEXT DEFAULT (date('now')),
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);
"""


@dataclass
class ContactHealth:
    contact_id:         str
    name:               str
    health_score:       float        # 0.0 – 1.0
    days_since_contact: int
    open_opportunities: int
    opportunity_value:  float
    suggested_action:   str


class CRMIntelligenceSystem:
    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # ── Data ingestion ────────────────────────────────────────────────────────

    def add_contact(self, contact_id: str, name: str, company: str = "", email: str = "") -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO contacts (id, name, company, email) VALUES (?,?,?,?)",
            (contact_id, name, company, email),
        )
        self._conn.commit()

    def log_interaction(
        self,
        contact_id:  str,
        type_:       str,
        summary:     str,
        occurred_at: Optional[str] = None,
    ) -> None:
        at = occurred_at or datetime.now().date().isoformat()
        self._conn.execute(
            "INSERT INTO interactions (contact_id, type, summary, occurred_at) VALUES (?,?,?,?)",
            (contact_id, type_, summary, at),
        )
        self._conn.commit()

    def add_opportunity(
        self,
        contact_id: str,
        title:      str,
        value_usd:  float = 0.0,
        stage:      str   = "prospect",
    ) -> None:
        self._conn.execute(
            "INSERT INTO opportunities (contact_id, title, value_usd, stage) VALUES (?,?,?,?)",
            (contact_id, title, value_usd, stage),
        )
        self._conn.commit()

    # ── Analysis ──────────────────────────────────────────────────────────────

    def analyse_contact(self, contact_id: str) -> ContactHealth:
        contact = self._conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        if not contact:
            raise ValueError(f"Contact not found: {contact_id}")

        last_interaction = self._conn.execute(
            "SELECT MAX(occurred_at) as last FROM interactions WHERE contact_id = ?",
            (contact_id,),
        ).fetchone()["last"]

        days_since = 999
        if last_interaction:
            last_date = datetime.strptime(last_interaction, "%Y-%m-%d").date()
            days_since = (date.today() - last_date).days

        opps = self._conn.execute(
            "SELECT COUNT(*) as n, SUM(value_usd) as total FROM opportunities "
            "WHERE contact_id = ? AND stage != 'closed'",
            (contact_id,),
        ).fetchone()
        open_opps  = opps["n"] or 0
        opp_value  = opps["total"] or 0.0

        # Health score heuristic: decays with days since contact, boosts with open opps
        recency_score = max(0.0, 1.0 - days_since / 60.0)
        opp_boost     = min(0.3, open_opps * 0.1)
        health        = min(1.0, recency_score + opp_boost)

        if days_since > 45 and open_opps > 0:
            action = f"Urgent follow-up — {days_since}d since last contact with open opportunity"
        elif days_since > 30:
            action = f"Schedule check-in — {days_since}d since last contact"
        elif open_opps > 0:
            action = "Progress opportunity — recent contact, move to next stage"
        else:
            action = "Nurture — no open opportunities, maintain relationship"

        return ContactHealth(
            contact_id=contact_id,
            name=contact["name"],
            health_score=round(health, 2),
            days_since_contact=days_since,
            open_opportunities=open_opps,
            opportunity_value=opp_value,
            suggested_action=action,
        )

    def surface_at_risk_accounts(self, threshold_days: int = 30) -> list[ContactHealth]:
        """Return contacts with open opportunities not contacted in threshold_days."""
        rows = self._conn.execute("SELECT id FROM contacts").fetchall()
        at_risk = []
        for row in rows:
            try:
                health = self.analyse_contact(row["id"])
                if health.days_since_contact >= threshold_days and health.open_opportunities > 0:
                    at_risk.append(health)
            except ValueError:
                continue
        return sorted(at_risk, key=lambda h: h.days_since_contact, reverse=True)

    # ── AI-assisted outreach ──────────────────────────────────────────────────

    def draft_follow_up(self, contact_id: str, additional_context: str = "") -> str:
        """Draft a personalised follow-up email grounded in interaction history."""
        contact = self._conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        if not contact:
            raise ValueError(f"Contact not found: {contact_id}")

        interactions = self._conn.execute(
            "SELECT type, summary, occurred_at FROM interactions "
            "WHERE contact_id = ? ORDER BY occurred_at DESC LIMIT 5",
            (contact_id,),
        ).fetchall()

        opps = self._conn.execute(
            "SELECT title, stage FROM opportunities WHERE contact_id = ? AND stage != 'closed'",
            (contact_id,),
        ).fetchall()

        history = "\n".join(
            f"- {r['occurred_at']} [{r['type']}]: {r['summary']}"
            for r in interactions
        ) or "No recorded interactions."

        open_items = "\n".join(
            f"- {o['title']} (stage: {o['stage']})" for o in opps
        ) or "No open opportunities."

        prompt = (
            f"Write a short, personalised follow-up email for:\n"
            f"Name: {contact['name']}, Company: {contact['company'] or 'unknown'}\n\n"
            f"Recent interaction history:\n{history}\n\n"
            f"Open opportunities:\n{open_items}\n\n"
            f"Additional context: {additional_context or 'None'}\n\n"
            f"Requirements: friendly and direct, 3–4 short paragraphs, no filler phrases, "
            f"clear next step in the closing line. Do not invent specific facts."
        )

        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def generate_weekly_briefing(self) -> str:
        """Summarise pipeline health and recommended actions for the week."""
        all_contacts = self._conn.execute("SELECT id FROM contacts").fetchall()
        healths = []
        for row in all_contacts:
            try:
                healths.append(self.analyse_contact(row["id"]))
            except ValueError:
                continue

        if not healths:
            return "No contacts in CRM."

        urgent     = [h for h in healths if h.days_since_contact > 45 and h.open_opportunities > 0]
        at_risk    = [h for h in healths if 30 <= h.days_since_contact <= 45]
        healthy    = [h for h in healths if h.health_score >= 0.7]
        total_pipe = sum(h.opportunity_value for h in healths)

        lines = [
            "=== WEEKLY CRM BRIEFING ===",
            f"Total contacts: {len(healths)}  |  Pipeline value: ${total_pipe:,.0f}",
            "",
            f"URGENT ({len(urgent)} accounts — >45 days, open opportunity):",
        ]
        for h in urgent[:5]:
            lines.append(f"  • {h.name} — {h.days_since_contact}d since contact, "
                         f"${h.opportunity_value:,.0f} open")

        lines += [
            "",
            f"AT RISK ({len(at_risk)} accounts — 30–45 days):",
        ]
        for h in at_risk[:5]:
            lines.append(f"  • {h.name} — {h.days_since_contact}d since contact")

        lines += [
            "",
            f"HEALTHY ({len(healthy)} accounts with health ≥ 0.7)",
        ]
        return "\n".join(lines)


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    crm = CRMIntelligenceSystem()

    crm.add_contact("c1", "Alice Chen", "Apex Corp", "alice@apex.com")
    crm.add_contact("c2", "Bob Rivera", "Summit AI", "bob@summit.ai")
    crm.add_contact("c3", "Carol James", "Vertex Labs")

    crm.log_interaction("c1", "demo", "Showed agent platform, positive feedback",
                        (date.today() - timedelta(days=52)).isoformat())
    crm.log_interaction("c2", "call", "Discussed pricing, requested proposal",
                        (date.today() - timedelta(days=12)).isoformat())
    crm.log_interaction("c3", "email", "Initial outreach, no response",
                        (date.today() - timedelta(days=35)).isoformat())

    crm.add_opportunity("c1", "Enterprise Platform Licence", value_usd=48_000, stage="qualified")
    crm.add_opportunity("c2", "Starter Tier", value_usd=8_400, stage="proposal")
    crm.add_opportunity("c3", "Consulting Engagement", value_usd=15_000, stage="prospect")

    print(crm.generate_weekly_briefing())
    print()

    at_risk = crm.surface_at_risk_accounts(threshold_days=30)
    print(f"At-risk accounts: {[h.name for h in at_risk]}")

    if at_risk:
        print(f"\nDraft follow-up for {at_risk[0].name}:")
        draft = crm.draft_follow_up(at_risk[0].contact_id)
        print(draft[:400], "...")
