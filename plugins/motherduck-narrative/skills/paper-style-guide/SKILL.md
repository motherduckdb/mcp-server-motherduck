---
name: paper-style-guide
description: MotherDuck slide template library — canonical design tokens, the 24 templates by role, build-step animation convention, and rules for picking the right template for a given slide. Use whenever generating a Dive, editing Paper artboards, or building a slide-plan that maps content to templates. Pulls the user out of token-drift and template-misuse.
---

# Paper Slide Template Library — style guide

The Paper file `Slide Deck Template` contains 24 reusable artboards (1920×1080) in a single vertical column. This is the canonical reference for tokens, template roles, and conventions. Pull from this guide when:

- Generating a Dive's React/JSX (use the right template per slide)
- Building a `slide-plan.md` (assign templates to beats)
- Editing a Paper artboard (don't drift tokens)
- Reviewing a deck (audit against this guide)

## Design tokens (use these literally — no drift)

```
ground.cream        #F4EFEA   default light slide background
ground.charcoal     #383838   dark / emphasis slide background
text.dark           #383838   primary on light
text.light          #F4EFEA   primary on dark
text.muted.light    #888888   secondary on light
text.muted.dark     #A8A8A8   secondary on dark
accent.orange       #FF9538   THE accent — MotherDuck "duck" orange
accent.yellow       #FFDE00   chart / status
accent.teal         #50C7B7   chart / positive delta
accent.blue         #6FC2FF   chart / link
soft.border         #D6CDBE   dotted dividers, faint rules
code.window.header  #ECE5DD   terminal / code title bar
build-marker        #B8B0A4   the small `▸ N` annotations
```

Type:
- Aeonik Mono 700 (display + numerals) and Aeonik Mono 400 (eyebrow, meta, build markers)
- Inter (body, lead lines, italic taglines)
- JetBrains Mono (code, terminal output)
- **Never** fall back to `System Sans-Serif` — Paper occasionally introduces it; replace explicitly.

Layout:
- Top hairline rule: 4px `#FF9538`, absolute `top:60px, left:160px, right:160px`.
- Eyebrow: absolute `top:130px, left:160px`, 22px Aeonik Mono regular `#FF9538` letter-spacing 0.16em uppercase.
- Page counter: matching Y, right-aligned at `right:160px`, 22px Aeonik Mono regular `#888888` (or `#A8A8A8`) letter-spacing 0.16em.
- Footer: absolute `bottom:70px`, 20px Aeonik Mono regular muted, letter-spacing 0.16em uppercase.
- Padding: 120px block, 160px inline (canonical).
- Hard offset shadows: `-8px 8px 0 #383838` (cards) or `-10px 10px 0 #383838` (code windows). Always **down-left**, never down-right.
- Artboard height: 1080px. If content overflows, *reduce content size*, don't grow the artboard.

## Template catalog

| ID | Name | Role | When to use | Build steps (typical) |
|---|---|---|---|---|
| **T1** | Hero / Statement | Title slide, opening hook | Opening, "Questions?", any centered single-statement moment on dark ground | 2 |
| **T2** | Big-stat | Single huge number with caption | One stat is the slide. `00%` + 1-line attribution. | 2 |
| **T3** | Terminal-output frame | Live SQL/CLI output result | Scan/query/run with a numeric result and wall time. | 3 |
| **T4** | Code-block frame | Static code snippet with line numbers | Show code that's read, not run. | 1 |
| **T5** | Data-table frame | Leaderboard / comparison table | Multi-row scoreboards with one highlighted row. | per-row reveal |
| **T6** | Stat-comparison cards | 3 KPI cards with hard offset shadow | Small set of related stats; one card per metric. | 4 (title + 3) |
| **T7** | Section header | Act break / chapter divider | Between major sections; resets attention. | 2 |
| **T8** | Sequential statement stack | 3 stacked Inter statements, last in orange | Transition with a punchline; "we tried X, Y, Z. The answer was W." | 3 |
| **T9** | Title + progressive bullets | Title + lead + 3 bullets + KPI footer | Definition / explainer with supporting stats. | varies |
| **T10** | Stacked example pairs | Two eyebrow-question-code pairs | Compare two examples. Question dominates SQL. | 4 |
| **T11** | Architecture chip diagram | Rows of pill chips by category | Show a system's parts grouped by role. | 4 |
| **T13** | Before-after delta rows | `before → after` rows with delta chips | Show a change's measurable impact. | per-row |
| **T15** | Annotated chart + KPI footer | Line chart with reference line and callouts | Trends over time / iterations. | per-cycle |
| **T16** | Numbered list + bar chart | Big colored numerals + bar comparison | "Three things X does differently" + supporting chart. | 4 |
| **T17** | Quote / pull-quote | Vertical orange rule + quote + attribution | Quoted passage from external source. | 2 |
| **T18** | Two-column compare | Side-by-side BEFORE / AFTER columns | Wider compare than T13; bullets per side. | 3 |
| **T19** | Agenda / TOC | 6-row numbered list with page refs | Opening agenda or section preview. | 6 |
| **T20** | Speaker / about | Photo placeholder + name + bio + handles | Speaker introduction. | 4 |
| **T21** | Closing CTA | "Stay in touch" headline + 4 CTA cards + QR | End slide with links and QR. | 3 |
| **T22** | Process flow with arrows | 4 stage cards connected by → arrows | Sequential pipeline with timings per stage. | 5 |
| **T23** | Dark statement hero | Dark ground centered display + accent rule | Mid-deck emphasis statement (not opening). | 2 |
| **T8-Dark** | Sequential statement stack (dark) | Dark variant of T8 | Transition on dark ground. | 3 |

**Skipped IDs**: T12 (interactive chat trace), T14 (ERD diagram) — bespoke, not added to library.

## Conventions

### Build-step annotations
Every multi-state slide carries small `▸ 1`, `▸ 2`, `▸ N` markers next to each revealable group, in 11px Aeonik Mono `#B8B0A4` letter-spacing 0.05em. They tell the implementer how many `fadeIn(build >= n)` steps to wire. Do **not** add a `BUILDS · N` pill in the header — the user removed those intentionally.

### Placeholder convention
Templates use `[BRACKETED PLACEHOLDERS]` for content slots, `NN / NN` for page counters, `[LEFT FOOTER]` / `[RIGHT FOOTER]` for footer slots, `00%` / `Nx` / `0.0K` for stat values. Never `{{mustache}}` style.

### Mapping to Dives
Each template corresponds to a slide function in the Dive. The function should:
- Accept `{ build }: { build: number }` as its prop
- Wrap each revealable group in `<div style={fadeIn(build >= N)}>`
- Use the canonical tokens (import from a shared constants file or inline; never literal `#FF7169` etc.)
- Match the template's standard chrome (top rule, eyebrow, page counter, footer)

The Dive's `SLIDE_BUILD_COUNTS` array must match the per-slide build totals declared in the slide-plan.

## Anti-patterns

- **Don't invent new templates** when one fits — adding T8 ≈ T8b ≈ T8c clutters the library. Reuse T8 with different content.
- **Don't reach for color outside the palette.** If you need a "danger" color, use orange. If you need a "success" color, use teal. Don't introduce red.
- **Don't make every slide a hero.** A talk needs T1 sparingly — opening, mid-deck emphasis (use T23 for that), and close. Most slides should be T3–T16.
- **Don't add BUILDS · N pills, T## corner labels, or watermarks.** Paper's layer tree handles artboard naming.
- **Don't use ▸ N markers in user-facing exports** — they're authoring metadata, not deck content. Hide or remove before export.
