# Chapter 13 — AI Content and Media Systems

One source piece → multiple platform-native derivatives. Brand voice as a calibration parameter.

## Files

| File | Contract | Description |
|---|---|---|
| `content_multiplier.py` | Content Multiplier | Generate Twitter thread, LinkedIn post, newsletter section, YouTube script, email subjects from one source |
| `content_publisher.py` | Content Publisher | Schedule and display a multi-platform publishing calendar |

## Key principle

> Content teams do not have a writing problem — they have a throughput problem.
> The insight-to-distribution cycle consumes most of its time on mechanics.
> Agent systems handle the mechanics. Human judgment belongs at the strategy
> and quality-review gates, not in the formatting work.

## Quick start

```bash
pip install anthropic
python content_multiplier.py     # generates all formats from a sample article
python content_publisher.py      # shows a sample publishing calendar
```

Set your API key first:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Format selection guide

| Goal | Format | AI reliability |
|---|---|---|
| Thought leadership | Long-form post | Medium — voice drift risk |
| Brand awareness | Thread / carousel | Medium — hooks vary |
| Lead generation | Email sequence | High — volume task |
| SEO traffic | Blog post | High — research-driven |
| Community building | Newsletter | Medium — voice drift risk |
| Product education | Video script | High — structure stable |

## Important

Always include a human review gate before publishing AI-generated content.
Use the pipeline to reach a 90% draft fast; spend the remaining time on
the editorial judgment the AI cannot supply.
