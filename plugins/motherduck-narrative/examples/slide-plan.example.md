# Slide Plan — Catalog Context for Agents
*Generated 2026-04-30 · 25min · PyData Seattle*

## Arc
hook (1-2) → setup (3-5) → tension (6-9) → payoff (10-12) → close (13-14)

## SLIDE_BUILD_COUNTS
`[2, 3, 4, 2, 4, 4, 4, 3, 5, 4, 4, 4, 4, 1]`

## Slides

| # | Template | Beat label | Content | Builds | Notes |
|---|---|---|---|---|---|
| 1 | T1 | INTRO | "Catalog Context for Agents" + speaker handle. Opens on dark ground. | 2 | |
| 2 | T8 | BEAT 02 · TRANSITION | "Months making AI better at SQL." / "Tried bigger models. Better prompts. More tools." / "The answer was a better data model." (3rd orange) | 3 | |
| 3 | T9 | BEAT 03 · WHAT IS DABSTEP | DABstep — 450-question agentic SQL benchmark. Bullets: Real schemas / Hard questions / Public scoreboard. KPI: 76% / 47% / 450 | 4 | |
| 4 | T10 | BEAT 04 · THE HARD QUESTIONS | Two example pairs LLMs get wrong on raw schemas. SQL snippets show the JOIN/window-function failures. | 2 | flag: needs real SQL not lorem |
| 5 | T11 | BEAT 05 · OUR HARNESS | 4 chip rows: TABLES (5 chips) / METADATA (2) / PROMPTS (2) / TOOLS (3). Cat C uses orange (modified). | 4 | |
| 6 | T13 | BEAT 06 · COLUMN COMMENTS | Title BEFORE → AFTER. Rows: EASY 76 → 79 +3pts / HARD 47 → 52 +5pts / TOKENS 3.4K → 3.6K +6%. Insight: "Three lines of column comments. No prompt change." | 4 | |
| 7 | T11 | BEAT 07 · VIEWS | Same harness diagram with VIEWS layer added. Modified row in orange. | 4 | |
| 8 | T8 | BEAT 08 · TWITTER DETOUR | "V3 looked great on local benchmark." / "Then someone tweeted overfitting concerns." / "They were right." (orange) | 3 | |
| 9 | T15 | BEAT 09 · V4 ITERATION | Line chart: pass-rate climbs over 8 iterations, crosses DABstep Easy baseline at iter 8. KPI: ITERATIONS 8 / BEST 78.4% / BASELINE 76.0% | 5 | live data optional — pulls from `bench_runs` table |
| 10 | T16 | BEAT 10 · WHAT V4 DOES | 3 numbered: Builds views / Reads comments / Iterates. Bar chart V1-V4 on Hard split. | 4 | |
| 11 | T13 | BEAT 11 · CLOSING DELTAS | Final 3-row delta vs baseline. EASY 76 → 79 / HARD 47 → 52 / TIME 18min → 24min | 4 | |
| 12 | T5 | BEAT 12 · SCOREBOARD | Public leaderboard table; our row highlighted at row 4. | 4 | live data optional — pulls from leaderboard view |
| 13 | T23 | BEAT 13 · THESIS | "The data model IS the context." Dark ground emphasis. | 4 | |
| 14 | T1 | BEAT 14 · QUESTIONS | Hero "Questions?" + handle + repo URL | 1 | |

## Template usage summary
- T1: 2 (open + close)
- T8: 2 (transitions)
- T9: 1
- T10: 1
- T11: 2
- T13: 2
- T15: 1
- T16: 1
- T5: 1
- T23: 1

## Open questions
- Slide 4 needs real SQL pulled from `examples/hard-questions.sql` — currently lorem
- Slide 9 + Slide 12 are flagged for live MotherDuck data via Recharts — defer to manual iteration
- Slide 8 (Twitter detour) — keep or cut? Currently keep; review with narrative-arc-reviewer

## Format contract

This file is parsed by `/paper-from-plan` and `/paper-to-dive`. The contract:

- The `## Slides` table is the slide registry. Columns: `#`, `Template`, `Beat label`, `Content`, `Builds`, `Notes`. Order matters — slide 1 is row 1.
- The `Template` column must be one of T1–T23 or T8-Dark (see `paper-style-guide` skill for the catalog).
- The `Builds` column must match the `SLIDE_BUILD_COUNTS` array exactly. If they disagree, the array wins (`paper-to-dive` will flag).
- The `Notes` column is freeform. Cells with `live data` / `flag` / `optional` get surfaced by the downstream skills.
- `## SLIDE_BUILD_COUNTS` is a single line containing a JS array literal — paste-ready into the Dive.
