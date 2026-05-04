# Workflow — brief to published Dive

How the pieces of `motherduck-narrative` fit together. Five stages, with optional review/cleanup helpers and a final iteration loop for live data.

## The pipeline

```
brief.md
    │
    │  /slide-plan
    ▼
slide-plan.md ◄── narrative-arc-reviewer (review)
    │
    │  /paper-from-plan
    ▼
Paper project (artboards, one per slide) ◄── paper-cohesion-auditor
    │
    │  manual: pixel-perfect visual edits in Paper
    │
    │  /paper-to-dive
    ▼
dive.tsx (slide nav + build counter + per-slide JSX)
    │
    │  fill in any text + humanizer (prose pass)
    │  iterate: live MotherDuck data via Recharts (optional)
    │
    ▼
mcp__claude_ai_MotherDuck__save_dive
    │
    ▼
Published Dive
```

Always-on context (auto-pulled when relevant):
- `paper-style-guide` — Paper template tokens + the 24-template catalog
- `motherduck-design-system` — marketing-website design system (when web work is involved)

## Stage-by-stage

### 1. Add brief to context (manual)

Put `projects/<MMDD-slug>/brief.md` (or your preferred name — outline.md, draft.md) in your Claude Code session. Cover the beats you want to hit, the thesis, sources, key stats. Doesn't need to be slide-shaped — bullet points and paragraphs are fine.

### 2. `/slide-plan` — brief → slide plan

```
/slide-plan projects/0428-catalog-context-for-agents
```

What it does:
- Reads `brief.md` + any `script.md`, `draft.md`, `outline.md`
- Pulls the template catalog from `paper-style-guide`
- Proposes 12–18 slides, each with: template ID, beat label, content sketch, build-step count
- Writes `slide-plan.md` to the project directory
- Outputs the `SLIDE_BUILD_COUNTS` array

The plan is markdown. Iterate on it before moving on.

### 3. `narrative-arc-reviewer` (subagent — recommended)

Spawn it on the slide plan:

> "Review @projects/0428-.../slide-plan.md for narrative arc — return the punch list."

Returns a slide-level punch list (max 12 items), an ASCII arc diagram, and the top-3 fixes. Iterate on `slide-plan.md` based on its feedback.

### 4. `/paper-from-plan` — slide plan → Paper artboards

```
/paper-from-plan projects/0428-catalog-context-for-agents/slide-plan.md
```

What it does:
- Reads `slide-plan.md`
- For each slide entry, clones the right template from the library (T1–T23, T8-Dark)
- Stamps in the content from the sketch (eyebrow, title, body, stats, code)
- Lays the cloned artboards in a new vertical column in Paper

After this runs you have a draft visual deck — but not pixel-perfect. The next stage is manual.

### 5. Pixel-perfect Paper edits (manual)

Open the Paper file. For each slide:
- Tighten alignment, content sizing, vertical rhythm
- Drop in real images, screenshots, terminal captures
- Adjust per-slide variations the template doesn't support (a row of 4 instead of 3, a custom annotation, etc.)
- Verify the slide reads at presentation distance

This is the stage where the deck stops being procedurally generated and starts being a thing. Don't skip it.

### 6. `paper-cohesion-auditor` (subagent — recommended before generating the Dive)

If multiple agents (or people) have edited the Paper artboards, run the cohesion audit:

> "Run paper-cohesion-auditor on the Slide Deck Template file."

Detects token drift, header collisions, footer drift, font leaks. Reports a punch list, or fixes them in place if you say "fix it".

### 7. `/paper-to-dive` — Paper artboards → dive.tsx

```
/paper-to-dive projects/0428-catalog-context-for-agents/slide-plan.md
```

What it does:
- Reads `slide-plan.md` for slide order + `SLIDE_BUILD_COUNTS`
- For each artboard, calls `get_jsx` and wraps the content in a per-slide React function
- Replaces `▸ N` build markers with `fadeIn(build >= n)` wrappers
- Wires slide navigation: keyboard arrows + click-to-advance + back
- Replaces literal hex tokens with the canonical `C` constants

Output: a renderable `dive.tsx` with slide nav and build progression baked in.

### 8. Fill text + `humanizer` (recommended)

If any slide content was placeholder, fill it now. Then run `humanizer` on prose-heavy parts (callouts, quotes, italic taglines) to remove em-dash overuse, AI vocabulary, vague attributions, etc.

> "/humanize the body text in dive.tsx slide 7"

Skip for code, SQL, terminal output. Use it on anything readable.

### 9. Iterate: live MotherDuck charts via Recharts (optional)

For slides that should show live data — leaderboards that update with new submissions, line charts that pull from a `bench_runs` table, etc. — layer Recharts on top:

1. Pick the slide that should be live (e.g., the scoreboard)
2. Add a `useEffect` calling `mcp__claude_ai_MotherDuck__query` against your dataset
3. Replace the static SVG/inline data with a Recharts component
4. Re-save the Dive

Don't try to do this for every slide — only the ones where freshness matters. Static is fine for setup, examples, transitions.

### 10. Save to MotherDuck

```
mcp__claude_ai_MotherDuck__save_dive
```

The Dive lives at `app.motherduck.com/dives/<slug>-<uuid>`.

## Reference skills (always-on)

- **`paper-style-guide`** — pulled when generating Dives, editing Paper, or building slide plans. Source of truth for tokens and templates.
- **`motherduck-design-system`** — pulled when editing `packages/mkt`, `packages/ui`, or any web page that references the Dive. Source of truth for site fonts, colors, primitives.

## Common deviations

- **Skipping the slide plan**: you lose the structural review and the build-count audit. Don't.
- **Skipping the narrative-arc reviewer**: fine for short Dives (<6 slides). For talks (12+ slides), don't skip — structural problems are 10× cheaper to fix in the plan than in JSX.
- **Skipping `/paper-from-plan` and going straight to Dive code**: you lose the visual iteration loop. Possible but only for very simple decks (e.g., all T1/T2/T3).
- **Skipping the manual Paper edits**: the result will look procedurally generated. Don't ship without a pass.
- **Skipping `paper-cohesion-auditor`**: fine if only one person/agent has touched the Paper file. If multiple agents edited it (the common case), run it.
- **Running humanizer on the whole file**: heavy-handed; it'll touch code comments and template names. Run it on text spans.

## When to update this plugin

If your workflow drifts (e.g., you're consistently editing `slide-plan.md` to add a column the skill doesn't generate), **update the skill**, not your workflow. PR the change to `mcp-server-motherduck` so the team gets it.
