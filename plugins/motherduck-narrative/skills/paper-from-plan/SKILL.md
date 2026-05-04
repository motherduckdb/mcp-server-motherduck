---
name: paper-from-plan
description: Convert a `slide-plan.md` into a set of Paper artboards — one per slide — by cloning the right templates from the slide library and stamping in the content sketches. Use after `/slide-plan` and before any pixel-perfect visual work in Paper. Pulls the 24-template catalog and canonical tokens from `paper-style-guide`.
disable-model-invocation: true
---

# paper-from-plan

Take a finalized `slide-plan.md` and build out the Paper artboards for the talk/Dive — one artboard per slide, each cloned from the right template in the library and stamped with the slide's content sketch.

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
3. **Stamp content** from the sketch:
   - Eyebrow text → set to `— [BEAT NN · <LABEL>]`
   - Page counter → set to `NN / TT` where TT is total slides
   - Title / display text → swap placeholder for the sketch's headline
   - Body / lead text → swap for the sketch's lead
   - Stat values → swap `00%` etc. with real values from the sketch
   - Code blocks → swap placeholder code for sketch code (if any)
   - Build markers `▸ N` → leave as-is (build wiring is handled by `/paper-to-dive`)
4. **Use `set_text_content`** for text swaps. Don't rewrite HTML structure unless the slide-plan demands a layout the template can't express (in which case flag and ask).

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
