# humanize-writing

A skill that makes AI-assisted text read like a person wrote it, while writing rather than only after the fact, plus a deterministic linter that scores any text for AI-pattern density.

Most tools in this space rewrite finished text. This one works in both directions: it shapes prose *as it's generated* so the patterns never appear, and it cleans existing text when you paste some in. It knows a cold email shouldn't be humanized like a formal report, it can learn *your* voice from a few paragraphs of your writing, and it ships with a stdlib-only Python linter you can run in CI.

It is not tied to any one assistant. The skill is plain Markdown in the open [Agent Skills](https://agentskills.io) format, so it works in Claude Code, Cursor, GitHub Copilot, Codex CLI, Amp, and any other harness that reads a `SKILL.md`. The linter is a standalone script that needs nothing but Python.

Grounded in primary sources: Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup), checked against the page as of September 2026, and the corpus studies it cites: Kobak et al. on excess vocabulary across 15M+ PubMed abstracts ([*Science Advances*, 2025](https://doi.org/10.1126/sciadv.adt3813)), Juzek & Ward on why models "delve" ([ACL 2025](https://arxiv.org/abs/2412.11385)), Reinhart et al. on grammatical and rhetorical style ([*PNAS*, 2025](https://doi.org/10.1073/pnas.2422455122)), and Russell et al. on what expert human detectors notice ([ACL 2025](https://arxiv.org/abs/2501.15654)).

## Install

**Any agent, via the skills CLI** (installs into Claude Code, Cursor, Copilot, Codex, and others; it detects what you use):

```
npx skills add shir-danishyar/humanize
```

**Manual, for any harness that reads SKILL.md.** Clone it into wherever your tool looks for skills:

```
git clone https://github.com/shir-danishyar/humanize.git
# e.g. ~/.claude/skills/humanize-writing, ~/.cursor/skills/humanize-writing, ...
```

**Claude Code specifically**, as a plugin:

```
/plugin marketplace add shir-danishyar/humanize
/plugin install humanize-writing@humanize
```

Whatever the harness, the skill is the same three Markdown files; `AGENTS.md` at the repo root tells any agent how to load and apply it.

## The `/humanizer` command

Once the plugin is installed in Claude Code, you also get a slash command:

```
/humanize-writing:humanizer <paste text, or a file path>
```

It runs the skill in rewrite mode on whatever you give it and returns only the humanized text (or edits the file in place, prose only). Claude Code namespaces plugin commands, hence the `humanize-writing:` prefix. If you want a bare `/humanizer`, copy the command file into your personal commands folder; it is self-contained and works without the plugin:

```
curl -fsSL https://raw.githubusercontent.com/shir-danishyar/humanize/main/commands/humanizer.md \
  -o ~/.claude/commands/humanizer.md
```

The skill itself stays automatic for audience-facing writing; the command is for when you want to point it at a specific piece of text.

## Usage

**Generation mode (default).** Once installed, the skill applies automatically to audience-facing writing tasks: emails, posts, articles, marketing copy, reports. Ask for the writing; it comes out without the patterns.

> Write a launch announcement for our new invoicing feature.

**Rewrite mode.** Paste existing text and ask for it to be cleaned. Quotes, citations, numbers, and proper nouns are preserved verbatim; only the patterns go.

> Humanize this. Keep the quotes and stats exactly as they are: [pasted draft]

**No invented facts.** In both modes the skill never adds a number, name, date, or quote that you didn't supply. If a sentence needs a specific it doesn't have, it asks or writes the sentence without it. A made-up statistic is worse than a vague sentence, because it is wrong.

**Register awareness.** The skill detects whether it's writing a LinkedIn post, an email, an article, or a formal report, and adjusts what "human" means for each (contractions and fragments in social posts, neither in formal documents). You can also state the register explicitly.

## The pattern catalog

39 patterns, each documented with a full before/after pair in [references/patterns.md](references/patterns.md). Every "after" uses only information already present in the "before", because that is what an honest rewrite looks like. The one-line versions:

| # | Pattern | Before | After |
|---|---------|--------|-------|
| P1 | Negative parallelism | The library isn't just a place to borrow books. It's a hub that hosts a homework club. | The library lends books and hosts a homework club. |
| P2 | Not only... but also | Not only shortens the trip but also runs every fifteen minutes. | Shortens the trip and runs every fifteen minutes. |
| P3 | Rule of three | Fast, friendly, and professional care, with same-day appointments for under-fives. | Same-day appointments for children under five. |
| P4 | False ranges | Everything from basic knife skills to advanced pastry: knife work, stocks, bread, laminated dough. | Knife work, stocks and sauces, bread, and laminated dough. |
| P5 | Significance participles | ...added a second platform in 1998, reflecting its growing importance. | ...added a second platform in 1998. |
| P6 | Copula avoidance | The hall serves as the polling station and boasts seating for 120. | The hall is the polling station and seats 120. |
| P7 | Synonym cycling | The bakery... the shop... the business... the establishment... | The bakery... it... |
| P8 | Staccato drama | One river. Three bridges. Zero closures in forty years. | The river's three bridges have not been closed in forty years. |
| P9 | Hedging stacks | Could potentially help reduce waiting times in some cases. | May reduce waiting times. |
| P10 | Wordiness (not an AI sign) | In order to renew a permit, bring proof of address. | To renew a permit, bring proof of address. |
| P11 | Uniform rhythm | Three same-shape sentences in a row. | Long sentence, then a short one. Like this. |
| P12 | Echo restatement | Closes in March. Won't be open in March. Unavailable that month. | The pool closes for maintenance in March. |
| P13 | Compulsive summaries | ...recommended Mill Road. In conclusion, Mill Road emerged as the recommendation. | ...recommended Mill Road, the only site on a bus route. |
| P14 | Editorializing filler | It's important to note that the footpath is closed until April. | The footpath is closed until April. |
| P15 | Vague attribution | Experts agree... industry reports, including the council's 2024 inspection... | The council's 2024 inspection found... |
| P16 | Overgeneralization | Widely regarded as the standard; a 2019 review recommended it. | A 2019 review in the Journal of Hydrology recommended it. |
| P17 | Significance inflation | The bypass opened in 2003, marking a pivotal moment and setting the stage for growth. | The bypass opened in 2003. |
| P18 | Promotional puffery | Nestled in the heart of the Peak District, the award-winning inn boasts a rich heritage dating to 1780. | The inn is in the Peak District and dates to 1780. |
| P19 | Challenges-and-outlook | Membership fell to 26. Despite these challenges, the choir is well-positioned for growth. | Membership fell from 40 to 26 after the hall closed. |
| P20 | Definition and announcement openers | Composting is the process by which... Let's dive into how to start. | A compost bin needs equal amounts of green and brown waste. |
| P21 | Sycophantic openers | Great question! You're absolutely right that drainage matters. | Clay soil holds water for days after rain. |
| P22 | Fake-candid openers | Honestly? Here's the thing: most seedlings die from overwatering. | Most seedlings die from overwatering. |
| P23 | Chatbot closers | ...booked for 14 June. I hope this helps! Let me know if you need anything else. | ...booked for 14 June. |
| P24 | Collaborative offers | Would you like me to also draft the sign-up form? | (nothing; the piece just ends) |
| P25 | Cutoff disclaimers and gap-filling | Details are not widely documented, but she likely grew up locally. | (cut; state the fact only if a source gives it) |
| P26 | Placeholder text | Join us on [date] at [venue] for the plant sale. | Join us on 4 May at the village hall. (from the writer, never guessed) |
| P27 | Em dash overuse | The ferry — which runs hourly — stops at two islands — Bryher and Tresco. | The ferry runs hourly and stops at Bryher and Tresco. |
| P28 | Bold mid-sentence | Bring **photo ID**, **proof of address**, and your **old permit**. | Bring photo ID, proof of address, and your old permit. |
| P29 | Term-colon bullets | **Parking:** free after 6pm. **Access:** step-free. | Parking is free after 6pm, and there is step-free access. |
| P30 | List compulsion | What to bring: • water • a sun hat • the form | Bring water, a sun hat, and the signed form. |
| P31 | Emoji formatting | ## 🌱 Spring planting | ## Spring planting |
| P32 | Title-case headings | ## How To Register Your Allotment | ## How to register your allotment |
| P33 | Skeleton overkill | A 250-word notice with a title heading, four sections, and rules between them. | The same 250 words as two paragraphs. |
| P34 | Quote mixing | Both “curly” and "straight" in one document. | One style, used consistently. |
| P35 | AI vocabulary | Showcases a vibrant tapestry of local cheeses, underscoring the rich heritage. | Local cheese, cider, and bread are the focus of the festival. |
| P36 | Stock idioms | At the end of the day, a good night's sleep is a testament to good habits. | People with regular habits sleep better. |
| P37 | Canned notability (2025+) | Featured in national media outlets and maintains an active social media presence. | The BBC and The Guardian have covered her work. |
| P38 | Vague association (2025+) | Associated with the orchestra, which he founded in 1994. | Founded the orchestra in 1994. |
| P39 | Unnecessary small tables | Founded \| 1911 / Members \| 240 | The club was founded in 1911 and has 240 members. |

The full banned-word list with plain replacements, including how the list has shifted between model generations, is in [references/vocabulary.md](references/vocabulary.md). The catalog also carries Wikipedia's list of signs of *human* writing, which the skill uses as permission slips: plain "is" and "has", definite statements, a single hedge, the odd unglamorous detail.

## A complete example

**Before**, a bakery's "about us" draft with the patterns left in. Read it once and try to list what you actually learned about the bakery:

<!-- lint:before-example:start -->
> In today's fast-paced world, bread isn't just food — it's a connection to something real. Nestled in the heart of the old town, Hollow Way Bakery stands as a testament to the enduring power of craft. Founded in 2011 by sisters Ana and Ruth Kaminski, the bakery embarked on its journey with a single second-hand oven from Leeds, leveraging time-honoured techniques to deliver an unparalleled experience for bread lovers everywhere.
>
> Our meticulous 36-hour sourdough process showcases our unwavering commitment to quality, while our vibrant range of loaves — from rustic rye to artisan baguettes — caters to every palate, with prices ranging from £3 to £5.50. It's important to note that we open at 7am and are closed on Mondays. In 2019, we opened a second location on Bank Street, marking a pivotal moment in our story; with six tables and freshly brewed coffee, it serves as a beloved community hub.
>
> Key highlights:
> - **Team:** 14 passionate bakers and front-of-house staff
> - **Sustainability:** Unsold bread goes to the night shelter every evening
> - **Heritage:** Rye loaves baked every Thursday, just like Grandma did
> - **Convenience:** Seamless pre-orders by phone before 4pm the day before
>
> Ultimately, Hollow Way isn't just a bakery. It's a family. We can't wait to welcome you!
<!-- lint:before-example:end -->

**After**, the same bakery, humanized. Every fact below was already in the draft above; nothing was added. This exact text is extracted and linted in CI, and a second test checks that it introduces no number the "before" didn't have:

<!-- lint:after-example:start -->
Hollow Way Bakery opened in 2011 in the old town. Ana and Ruth Kaminski, who are sisters, started it with one second-hand oven from Leeds and still run it.

The sourdough takes 36 hours from mixing to the oven. Rye is baked on Thursdays, to the recipe the sisters' grandmother used, and there are baguettes every day. Loaves cost between £3 and £5.50. We open at 7am and we're closed on Mondays.

A second shop opened on Bank Street in 2019. It has six tables and serves coffee, so it's the one to come to if you want to sit down. Between the two shops, 14 people work here, in the bakery and behind the counters.

If you need a particular loaf, phone the shop before 4pm the day before and we'll set it aside. Whatever bread is left at closing goes to the night shelter that evening, so we'd rather you ordered than we guessed.

If you want the rye, come on a Thursday.
<!-- lint:after-example:end -->

The first version tells you the bakery is a testament to the enduring power of craft. The second tells you when it opened, what it bakes, what a loaf costs, when to come, and what happens to the bread nobody bought. Same facts, in both. One of them you could act on.

## The linter

`scripts/ai_pattern_lint.py` is a deterministic checker for the mechanically detectable patterns. Python 3.9+, standard library only, no installation.

```
python3 scripts/ai_pattern_lint.py draft.md          # lint a file
cat draft.txt | python3 scripts/ai_pattern_lint.py    # or stdin
python3 scripts/ai_pattern_lint.py --json draft.md    # machine-readable
python3 scripts/ai_pattern_lint.py --threshold 3 *.md # stricter gate
```

Output (run against the "before" cold email in `tests/fixtures/pairs/01-before.txt`):

```
tests/fixtures/pairs/01-before.txt:1: P35 ai-vocabulary: “Seamless”
tests/fixtures/pairs/01-before.txt:5: P1 negative parallelism: “isn't just”
tests/fixtures/pairs/01-before.txt:5: P36 stock phrase: “In today's fast-paced world”
tests/fixtures/pairs/01-before.txt:7: P14 stock phrase: “It's important to note”
tests/fixtures/pairs/01-before.txt:7: P27 em dash over budget: “em dash #2+ (allowed 1 per 145 words)”
tests/fixtures/pairs/01-before.txt:7: P35 ai-vocabulary: “leverage”
...
tests/fixtures/pairs/01-before.txt:9: P23 stock phrase: “feel free to reach out”
tests/fixtures/pairs/01-before.txt:9: P35 ai-vocabulary: “delve”

145 words, 17 hits, density 117.2/1000 words (threshold 5) → FAIL
```

It exits 0 when density (hits per 1000 words) is under the threshold and 1 otherwise, so it drops straight into CI. This repo runs it on its own documentation: the worked example above and every `*-after.txt` fixture must lint clean or the build fails.

What it checks: banned vocabulary (following Wikipedia's current words-to-watch list), negative parallelism, "not only... but also", rule-of-three lists, trailing significance participles ("...reflecting its", "...ensuring the"), hedging stacks, copula avoidance ("serves as a"), editorializing and vague-attribution phrases, significance and legacy phrases, summary openers, chatbot openers and closers, knowledge-cutoff disclaimers and speculative gap-filling, canned media-coverage claims, em-dash frequency, sentence-initial connective pile-ups, repeated "associated with" hedging, `**Term:**` bullets, emoji in headings, and curly/straight quote mixing. Markdown code blocks are skipped.

What it deliberately does not flag: "in order to", "due to the fact that", and other ordinary wordiness. Wikipedia lists these among the constructions *more* common in human writing than in AI output. Trim them for concision if you like, but a linter that punished them would push text toward AI, not away from it.

What it can't check: false ranges, synonym cycling, echo restatement, register mismatches, invented facts. Those are the judgment calls. The skill handles them; the linter is the smoke detector, not the fire department.

## Voice calibration

Cleaned text is neutral text, and neutral is nobody's voice. Give the skill 2–3 paragraphs of your real writing and it extracts a profile (sentence-length mix, punctuation habits, favorite transitions, formality) and writes with that instead:

> Here are two emails I sent last week. Match my voice from now on: [samples]

The profile is saved to `voice-profile.md` in your project, so it persists across sessions; any future session that finds the file applies it automatically. Details in [references/voice.md](references/voice.md).

## False positives

These patterns are statistical signals, not proof. Humans write em dashes and three-item lists too; the tell is density, not existence. Wikipedia also keeps a list of things that are *not* signs, which the skill honours: perfect grammar, a mix of casual and formal register, prose that merely feels bland, formal vocabulary in general, one transition word, unsourced claims, curly quotes on their own. The skill never edits quoted third-party text, never trades factual precision for style, and if you explicitly ask for bullets or em dashes, you win. The same caution applies to the linter: a score above threshold means "look closer", not "written by AI".

## References

- Wikipedia, [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The WikiProject AI Cleanup field guide this skill's patterns are drawn from. Checked against the September 2026 revision.
- Kobak, D., González-Márquez, R., Horvát, E.-Á., & Lause, J. (2025). [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://doi.org/10.1126/sciadv.adt3813). *Science Advances* 11(27). The 15M-abstract corpus study behind the vocabulary list (preprint: arXiv:2406.07016).
- Juzek, T. S., & Ward, Z. B. (2025). [Why does ChatGPT "delve" so much? Exploring the sources of lexical overrepresentation in large language models](https://arxiv.org/abs/2412.11385). ACL 2025.
- Reinhart, A., et al. (2025). [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://doi.org/10.1073/pnas.2422455122). *PNAS* 122(8). Source for the trailing-participle and copula-avoidance findings.
- Russell, J., Karpinska, M., & Iyyer, M. (2025). [People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text](https://arxiv.org/abs/2501.15654). ACL 2025. What expert human detectors actually notice.
- [The rise and fall of LLM fingerprints](https://arxiv.org/abs/2502.09606) (arXiv:2502.09606). Vocabulary fingerprints shift between model generations, which is why the word list is dated by era.

## Changelog

**v2.1.1** (2026-09)
- `/humanizer` slash command (`commands/humanizer.md`): explicit rewrite-mode entry point for pasted text or a file; self-contained so it also works as a personal command without the plugin

**v2.1.0** (2026-09)
- Re-checked every pattern against the September 2026 revision of Wikipedia's "Signs of AI writing"
- Three new patterns from that page: canned notability and media-coverage claims (P37), vague association (P38), unnecessary small tables (P39)
- "No invented facts" is now an explicit rule in both modes; every before/after example in the catalog and the README was rewritten so the "after" adds nothing the "before" didn't contain, and a test enforces this for numbers
- Vocabulary list dated by model era (2023 / mid-2024 / mid-2025), with the words newer models have dropped and the per-model differences Wikipedia records
- Wordiness ("in order to", "the fact that") reclassified: Wikipedia lists it as a sign of human writing, so the linter no longer flags it
- Linter: significance-participle list expanded to Wikipedia's "superficial analyses" verbs; new phrase checks for significance, notability, gap-filling, and chatbot language; budgeted checks for connective pile-ups and "associated with"
- Signs of human writing and Wikipedia's list of ineffective indicators added to the catalog and the false-positive guard
- Repository moved to `shir-danishyar/humanize`

**v2.0.0** (2026-07)
- Rewrite mode with hard preservation rules for quotes, citations, numbers, and proper nouns
- Register detection (social / email / editorial / formal)
- Pattern catalog restructured into `references/` with 36 numbered patterns
- Voice calibration with a persistent `voice-profile.md`
- `scripts/ai_pattern_lint.py`: deterministic linter with density scoring, JSON output, and CI exit codes
- Test suite and GitHub Actions workflow; the README's own examples are linted in CI
- Claude Code plugin + marketplace manifests; `npx skills add` compatibility

**v1** (unreleased)
- Single-file SKILL.md: generation-time rules, banned vocabulary, formatting rules, 10-point self-audit

## License

MIT
