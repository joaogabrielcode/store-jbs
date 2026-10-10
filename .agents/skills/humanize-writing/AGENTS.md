# Instructions for agent harnesses

This repository is an [Agent Skills](https://agentskills.io)-format skill. To use it:

1. Load `SKILL.md` at the repo root. Its frontmatter `description` tells you when the skill applies: any audience-facing prose task (emails, posts, articles, marketing copy, reports), or an explicit request to humanize or de-AI text.
2. Follow SKILL.md's workflow. It will direct you to read the files under `references/` on demand — `patterns.md` for the full pattern catalog, `vocabulary.md` for word substitutions, `voice.md` when the user provides writing samples or a `voice-profile.md` exists. Don't preload them; they're structured for progressive disclosure.
3. Optionally verify output mechanically: `python3 scripts/ai_pattern_lint.py <file>` reports AI-pattern density (exit 0 = clean). Python 3.9+, no dependencies.

Two rules bind harder than the rest: never invent a fact, number, name, or quote that the source or the user did not supply; and when rewriting a file, change only the prose (leave code, front matter, data, and link targets alone).

Do not apply this skill to code, commit messages, configuration, or legal text. User instructions always override the skill's defaults.
