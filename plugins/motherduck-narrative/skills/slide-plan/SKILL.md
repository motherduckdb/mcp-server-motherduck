---
name: slide-plan
description: Convert a talk brief (or draft, or sketch) into a slide-by-slide plan that maps each beat to a Paper template, build-step count, and content sketch. Writes `slide-plan.md` to the project directory. Use when starting a new talk/Dive after the brief is drafted, before any visual or implementation work.
disable-model-invocation: true
---

# slide-plan

Turn a brief into a structured slide plan. Output is a `slide-plan.md` table that drives the Paper template work and the Dive implementation.

See [examples/brief.example.md](../../examples/brief.example.md) for an example brief, and [examples/slide-plan.example.md](../../examples/slide-plan.example.md) for the exact output format expected by downstream skills.

## Inputs

The user invokes with a project directory or brief path:
- `/slide-plan projects/0428-catalog-context-for-agents`
- `/slide-plan projects/<slug>/brief.md`

If no path given, prompt for one.

## Workflow

### 1. Read the inputs
- The outline (`brief.md`, `circulation-brief.md`, or whatever file the user pointed at)
- Any existing `script.md`, `draft.md` to ground the plan in real content
- The project's `brief.md` if it exists (audience, length, venue)

### 2. Pull template catalog
Reference `paper-style-guide` skill for the 24-template catalog. Don't re-list it here — the catalog is the source of truth for which template fits which beat.

### 3. Propose a slide-by-slide plan
Aim for ~12–18 slides for a 25-minute talk; ~8–12 for a 15-minute talk. Don't over-stuff. Each entry must have:
- **Slide #** (1-indexed)
- **Template** (T## — pick the best fit; default to T1/T7/T8/T16/T22 sparingly)
- **Beat label** (the eyebrow text, e.g., `BEAT 04 · THE HARD QUESTIONS`)
- **Content sketch** (2-3 lines describing what's on the slide — actual headline + supporting line, not generic)
- **Build steps** (integer; matches the template's typical pattern)
- **Notes** (optional — open questions, missing assets, "needs chart")

### 4. Write `slide-plan.md`

Format:

```markdown
# Slide Plan — <talk title>
*Generated <date> · <talk length>min · <audience>*

## Arc
hook (1-2) → setup (3-5) → tension (6-9) → payoff (10-12) → close (13-14)

## SLIDE_BUILD_COUNTS
`[2, 3, 4, 2, 4, 4, 8, 4, 3, 5, 4, 4, 4, 1]`

## Slides

| # | Template | Beat label | Content | Builds | Notes |
|---|---|---|---|---|---|
| 1 | T1 | — INTRO | "Talk title" + speaker handle. Opens with the question. | 2 | |
| 2 | T8 | BEAT 02 · TRANSITION | Three statements; last in orange — "we tried X. We tried Y. The answer was Z." | 3 | |
| 3 | T9 | BEAT 03 · WHAT IS DABSTEP | Title + lead + 3 bullets + KPI footer (76% / 47% / 450) | 4 | |
| ... |

## Template usage summary
- T1: 2 (open + close)
- T8: 1 (transition)
- T9: 1
- T15: 2
...

## Open questions
- Does slide 7 need a screenshot of X?
- Slide 10 KPI value not yet measured.
```

### 5. Output the SLIDE_BUILD_COUNTS array

Below the table, output the build-counts array as a single line ready to paste into the Dive's source:

```
const SLIDE_BUILD_COUNTS = [2, 3, 4, 2, 4, 4, 8, 4, 3, 5, 4, 4, 4, 1];
```

The order must match the slide table order exactly.

### 6. Save and report
Write to `<project-dir>/slide-plan.md`. Tell the user the file path, the slide count, and the total build-step count (sum of the array). Recommend running the `narrative-arc-reviewer` subagent on the result before moving to Paper / Dive implementation.

## Quality bar

- **Content sketches must be specific.** "Show stats" is wrong — "76% Easy / 47% Hard / 450 Q's" is right. Pull from the brief.
- **Don't repeat templates** without reason. If T9 appears 5 times, the deck is monotonous. Mix.
- **Map dependencies in the arc.** A payoff slide can't precede its setup. If you find this, fix the order.
- **Default to fewer slides.** 18 slides in 25 minutes = 1:23 each. That's fast. If beats are dense, cut, don't shrink.

## Anti-patterns

- Don't generate placeholder slide content (lorem ipsum). Pull real beats from the brief. If the brief doesn't have content for a beat, list it under "Open questions".
- Don't propose new template IDs (T24, T25...). Use the existing 24.
- Don't write the Dive JSX here — that's `dive-from-plan`'s job.
- Don't auto-invoke `narrative-arc-reviewer` — recommend it; let the user decide.
