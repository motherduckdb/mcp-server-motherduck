---
name: paper-from-plan
description: Convert a `slide-plan.md` into a set of Paper artboards — one per slide — by cloning the right templates from the slide library and stamping in the content sketches. Use after `/slide-plan` and before any pixel-perfect visual work in Paper. Pulls the 24-template catalog and canonical tokens from `paper-style-guide`.
disable-model-invocation: true
---

# paper-from-plan

Take a finalized `slide-plan.md` and build out the Paper artboards for the talk/Dive — one artboard per slide, each cloned from the right template in the library and stamped with the slide's content sketch.

See [examples/slide-plan.example.md](../../examples/slide-plan.example.md) for the exact format this skill parses.

This is the bridge between the structured plan (markdown) and the visual artifact (Paper). After this skill runs you'll do pixel-perfect edits in Paper before exporting to a Dive via `/paper-to-dive`.

## Inputs

```
/paper-from-plan projects/<slug>/slide-plan.md
/paper-from-plan projects/<slug>/slide-plan.md --paper-file "Talk Title"
```

If `--paper-file` isn't given, prompt the user to open the destination Paper file in the desktop app, then call `mcp__plugin_paper-desktop_paper__get_basic_info` to confirm.

## Workflow

### 1. Load context
- Call `mcp__plugin_paper-desktop_paper__get_guide({ topic: "paper-mcp-instructions" })` once.
- Read `slide-plan.md` and parse the slide table (slide # / template T## / beat label / content sketch / build count).
- Pull canonical tokens + per-template patterns from `paper-style-guide`.

### 2. Locate template source artboards
The team's `Slide Deck Template` Paper file holds the 24 reference templates (T1–T23 + T8-Dark) at `left: 530px` in a vertical column. Use `get_basic_info` to enumerate artboards. Build a map from template ID → source artboard ID.

If a slide-plan entry references a template not in the library (e.g., T24, T-Custom), flag it and skip — don't invent.

### 3. For each slide in the plan
Per slide:
1. **Clone the template**. Use `mcp__plugin_paper-desktop_paper__duplicate_nodes` on the source artboard. Position the clone in a new vertical column at `left: 2530` (offset from the template library) at the appropriate `top` (1160px stride starting at -300, matching the template column convention).
2. **Rename** the cloned artboard to `Slide N · <beat label>` via `rename_nodes`.
3. **Discover content nodes by name**. Templates use stable layer names — use `get_children` recursively (or `get_tree_summary`) on the cloned artboard to find them. Common names: `Eyebrow`, `Page counter`, `Title block`, `Title`, `Lead`, `Statements`, `Bullets`, `KPI footer`, `Pair 1` / `Pair 2`, `Rows`, `Header`, `Footer`. The `descendantIdMap` returned by `duplicate_nodes` lets you translate a known source-template node ID into the cloned equivalent — use it where possible to avoid re-discovery.
4. **Stamp content** from the sketch using the per-template cheat sheet below. Use `set_text_content` for text-only swaps. Don't rewrite HTML structure unless the slide-plan demands a layout the template can't express (in which case flag and ask).
5. **Leave alone**: top hairline rule, footer chrome, build markers `▸ N`, dotted dividers, hard-offset shadows. The template provides these — don't touch.

#### Per-template content-mapping cheat sheet

| Template | Slots to fill |
|---|---|
| **T1** Hero | Eyebrow, Title (display, may use `\n` to balance lines), Page counter |
| **T2** Big-stat | Eyebrow, Big number (digit text), Big number (unit text — often `%`), Caption (multi-line OK), Footer attribution |
| **T3** Terminal | Eyebrow, Window title (`~/PATH · ENGINE Vn.n`), Code line, Result number, Result caption (`↳ ROWS · MB/s · THREADS`), Wall-time value |
| **T4** Code-block | Eyebrow, Window title (filename), Window subtitle (LANGUAGE · RUNTIME), Code lines (one text node per line, preserve syntax-highlight color split if any) |
| **T5** Data-table | Eyebrow, Header row text, Data rows (one set of cells per row — label + value), Highlighted-row callout |
| **T6** Stat-cards | Eyebrow, Display headline, 3 cards (each: METRIC NAME, before→after subtitle, big stat value, description) |
| **T7** Section header | Page counter, Section label (top-right), Section name eyebrow (left), Display title (may be 2 lines via `\n`), Sub-context strip |
| **T8** Sequential | Eyebrow, 3 statement lines (3rd is orange), Page counter |
| **T9** Title+bullets | Eyebrow, Title, Lead body, 3 bullets (each: bold heading + supporting clause), 3 KPI labels + 3 KPI values |
| **T10** Stacked examples | Eyebrow, Pair 1 eyebrow, Pair 1 question, Pair 1 code-window title + code, Pair 2 same |
| **T11** Architecture | Eyebrow, Title, Subtitle, 4 rows (each: category label + chip set + count) |
| **T13** Delta rows | Eyebrow, Title, Subtitle, 3 rows (each: metric label + before value + after value + delta chip text), Footer insight |
| **T15** Annotated chart | Eyebrow, Title, Subtitle, SVG chart values (poly points + axis labels), 3 callout texts, 3 KPI cards |
| **T16** Numbered + chart | Eyebrow, Title, 3 numbered items (numeral stays, replace headline + body), Chart title, 4 bar values (`00%`), Tagline |
| **T17** Quote | Eyebrow, Quote body, Attribution |
| **T18** Two-col compare | Eyebrow, Title, Subtitle, Left col (eyebrow + headline + 4 bullets + KPI), Right col (same) |
| **T19** Agenda | Eyebrow, Title (`AGENDA`), 6 rows (each: number stays, name + page ref) |
| **T20** Speaker | Eyebrow, Display name, Role line, 3-paragraph bio, 4 handle chips |
| **T21** Closing CTA | Eyebrow, Headline, Lead body, 4 CTA cards (each: label + URL), QR placeholder |
| **T22** Process flow | Eyebrow, Title, 4 stage cards (each: stage name + body + KPI value), Footer tagline |
| **T23** Dark hero | Eyebrow, Display title (may use `\n`), Supporting italic line |
| **T8-Dark** | Same slots as T8, dark ground inherited from clone |

If the slide-plan content sketch has fewer items than the template provides (e.g., only 2 bullets but T9 has 3), leave unused slots with their placeholder text — don't delete them. The user fills them in pixel-perfect editing.

### 4. Verify
After all slides are placed, call `get_screenshot` on the first 2-3 cloned artboards to confirm the swaps landed cleanly. Don't audit the whole deck — that's `paper-cohesion-auditor`'s job.

### 5. Report
Return:
- Path to the Paper file with the new artboard column
- Slide count + total build count
- Any slide-plan entries that couldn't be mapped to a template
- Reminder: "Next step is pixel-perfect edits in Paper, then `/paper-to-dive`."

Call `mcp__plugin_paper-desktop_paper__finish_working_on_nodes` (no args).

## Quality bar

- **Use the canonical templates.** Don't write custom layouts — clone from the library and edit content. If a slide needs a layout the library doesn't have, flag it.
- **Don't drift tokens.** The cloned artboards inherit the template's tokens; don't override colors/fonts mid-clone. If you must, use canonical values from `paper-style-guide`.
- **Don't auto-invoke `paper-cohesion-auditor`.** Recommend it before `/paper-to-dive` if multiple agents have touched the file.
- **Match the talk's column position.** All cloned artboards for one talk live in their own vertical column at `left: 2530` (or further right if 2530 is occupied). Don't scatter.

## Anti-patterns

- Don't generate slide content beyond what's in the plan's content sketch. If the sketch says "lorem ipsum", the artboard says "lorem ipsum" — flag the slide for follow-up.
- Don't skip the dotted-divider, hairline rule, or footer chrome. Cloning the template preserves these — leave them alone.
- Don't write the Dive JSX here. That's `/paper-to-dive`'s job.
- Don't try to add slide navigation or build-state controls in Paper — those are runtime concerns handled in the Dive.
