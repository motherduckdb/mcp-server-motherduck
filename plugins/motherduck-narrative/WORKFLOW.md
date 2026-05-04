# Workflow — brief to published Dive

How the seven pieces of `motherduck-narrative` actually fit together. Read this once; refer back when something's unclear.

## The pipeline

```
brief.md
    │
    │  /slide-plan
    ▼
slide-plan.md ◄── narrative-arc-reviewer (review)
    │
    │  /dive-from-plan
    ▼
dive.tsx (skeleton with TODOs)
    │
    │  fill content manually
    │  + humanizer  (prose cleanup pass)
    │  + paper-cohesion-auditor  (Paper template QA before export)
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

### 1. Draft the brief (manual)

Write `projects/<MMDD-slug>/brief.md`. Cover the beats you want to hit, sources, any stats. Doesn't need to be slide-shaped yet — bullet points and paragraphs are fine.

### 2. `/slide-plan` — brief → slide plan

```
/slide-plan projects/0428-catalog-context-for-agents
```

What it does:
- Reads `brief.md` + any `script.md`, `draft.md`, `outline.md`
- Pulls the template catalog from `paper-style-guide`
- Proposes 12–18 slides, each with: template ID, beat label, content sketch, build-step count
- Writes `slide-plan.md` to the project directory
- Outputs the `SLIDE_BUILD_COUNTS` array ready to paste into the Dive

Output is a markdown table, not generated content. You'll iterate on it before moving on.

### 3. `narrative-arc-reviewer` (subagent — recommended)

Spawn it on the slide plan:

> "Review @projects/0428-.../slide-plan.md for narrative arc — return the punch list."

What it does:
- Reads the slide plan + brief
- Evaluates hook strength, setup → payoff symmetry, beat sequencing, redundancy, transitions, tension, ending power
- Returns a slide-level punch list (max 12 items), an ASCII arc diagram, and the top-3 fixes

Iterate on `slide-plan.md` based on its feedback. Re-run if you've made structural changes.

### 4. `/dive-from-plan` — slide plan → Dive skeleton

```
/dive-from-plan projects/0428-catalog-context-for-agents
```

What it does:
- Reads `slide-plan.md`
- Pulls canonical tokens + per-template stub patterns from `paper-style-guide`
- Generates `dive.tsx` with: build counter wiring, `SLIDE_BUILD_COUNTS` array, `fadeIn` helper, `SlideChrome` component, one stub per slide with the right number of `fadeIn(build >= n)` wrappers, and `// TODO` comments referencing the content sketch from the plan

Output is a skeleton, not a finished Dive. You fill in the content.

### 5. Fill in content (manual)

Replace each `// TODO` with real content. Keep using the canonical tokens — `paper-style-guide` is in context so Claude won't drift.

### 6. `humanizer` skill (recommended)

Run it on any prose-heavy parts (callouts, quotes, italic taglines, body lines):

> "/humanize the body text in dive.tsx slide 7"

What it does:
- Removes em-dash overuse, rule-of-three, inflated symbolism, vague attributions, AI vocabulary (delve, leverage, robust, etc.), negative parallelisms ("not just X, but Y")
- Returns cleaned prose

Skip it for code, SQL, terminal output. Use it on anything readable.

### 7. `paper-cohesion-auditor` (subagent — recommended before export)

If you've used Paper templates as the visual source of truth and you're about to export screenshots or hand off to design:

> "Run paper-cohesion-auditor on the Slide Deck Template file."

What it does:
- Enumerates artboards via the Paper MCP
- Detects token drift (`#FF7169` ≠ `#FF9538`, `#2D2D2D` ≠ `#383838`, etc.), header-row collisions, footer drift, font-family leaks, shadow direction mistakes, alignment / overflow
- Reports a punch list, OR (if you say "fix it") applies fixes via `update_styles` / `set_text_content` / `delete_nodes`

### 8. Save to MotherDuck

```
mcp__claude_ai_MotherDuck__save_dive
```

The Dive lives at `app.motherduck.com/dives/<slug>-<uuid>`.

## Reference skills (always-on)

These don't need to be invoked — they get pulled into context automatically when their topic comes up:

- **`paper-style-guide`** — pulled when generating Dives, editing Paper, or building slide plans. Source of truth for tokens and templates.
- **`motherduck-design-system`** — pulled when editing `packages/mkt`, `packages/ui`, or any web page that references the Dive. Source of truth for site fonts, colors, primitives.

## Common deviations

- **Skipping the slide plan**: you can go straight from brief to Dive, but you lose the structural review and the build-count audit. Don't.
- **Skipping the narrative-arc reviewer**: fine for short Dives (<6 slides). For talks (12+ slides), don't skip — structural problems are 10x cheaper to fix in the plan than in the JSX.
- **Running humanizer on the whole file**: heavy-handed; it'll touch code comments and template names. Run it on text spans.
- **Skipping the cohesion audit**: fine if only one person/agent has touched the Paper file. If multiple agents have edited it (the common case), run it.

## When to update this plugin

If your workflow drifts (e.g., you're consistently editing `slide-plan.md` to add a column the skill doesn't generate), **update the skill**, not your workflow. PR the change to `mcp-server-motherduck` so the team gets it.
