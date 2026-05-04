---
name: dive-from-plan
description: Generate a MotherDuck Dive JSX skeleton from a `slide-plan.md`. Wires SLIDE_BUILD_COUNTS, the slide registry, and one stub function per template-mapped slide using the canonical Paper tokens. Use after `slide-plan` has produced the plan and before fleshing out per-slide content. Saves the boilerplate so the user only fills in data.
disable-model-invocation: true
---

# dive-from-plan

Take a finalized `slide-plan.md` and produce the React/JSX skeleton of a MotherDuck Dive. The output is a `.tsx` file with all the boilerplate (build counter wiring, slide registry, fadeIn helper, per-slide function stubs) pre-filled — the user fills in the actual content.

## Inputs

```
/dive-from-plan projects/<slug>/slide-plan.md [--out projects/<slug>/dive.tsx]
```

If `--out` is omitted, write to `<project-dir>/dive.tsx`.

## Workflow

### 1. Read the plan
Parse `slide-plan.md` for:
- The slide table (slide # / template / beat label / content / builds)
- The `SLIDE_BUILD_COUNTS` array
- The talk title (from the `# Slide Plan — ...` heading)

### 2. Pull template style from `paper-style-guide`
Reference the canonical tokens and template roles. Don't drift. Use these as inline constants in the generated file:

```tsx
const C = {
  cream: '#F4EFEA',
  charcoal: '#383838',
  orange: '#FF9538',
  muted: '#888888',
  mutedDark: '#A8A8A8',
  yellow: '#FFDE00',
  teal: '#50C7B7',
  blue: '#6FC2FF',
  warmBorder: '#D6CDBE',
  codeHeader: '#ECE5DD',
};
```

### 3. Generate the dive file

Structure:

```tsx
// <Talk title>
// Generated from slide-plan.md on <date>
// Slides: <N>  ·  Total build steps: <sum>

import React, { useState, useEffect } from "react";

const C = { /* canonical tokens */ };

const SLIDE_BUILD_COUNTS = [/* from plan */];
const SLIDE_NAMES = [/* from plan, kebab-case */];

// fadeIn helper — opacity 0→1 over 0.4s, with hidden-skeleton fallback
const fadeIn = (visible: boolean): React.CSSProperties => ({
  opacity: visible ? 1 : 0,
  transition: "opacity 0.4s ease",
});

// Build/slide controller (keyboard arrows + click)
function useBuild(): { slide: number; build: number; advance: () => void; back: () => void } {
  // ... boilerplate keyboard handler reading SLIDE_BUILD_COUNTS ...
}

// Standard chrome — every slide gets these
function SlideChrome({ slideNum, totalSlides, eyebrow, dark }: {
  slideNum: number; totalSlides: number; eyebrow: string; dark?: boolean;
}) {
  const text = dark ? C.cream : C.charcoal;
  const muted = dark ? C.mutedDark : C.muted;
  return (
    <>
      <div style={{ position: 'absolute', top: 60, left: 160, right: 160, height: 4, background: C.orange }} />
      <div style={{ position: 'absolute', top: 130, left: 160, color: C.orange, fontFamily: 'Aeonik Mono', fontSize: 22, letterSpacing: '0.16em', textTransform: 'uppercase' }}>{eyebrow}</div>
      <div style={{ position: 'absolute', top: 130, right: 160, color: muted, fontFamily: 'Aeonik Mono', fontSize: 22, letterSpacing: '0.16em' }}>{`${String(slideNum).padStart(2, '0')} / ${String(totalSlides).padStart(2, '0')}`}</div>
      {/* footer slots */}
    </>
  );
}

// One function per slide
function Slide01_<KebabName>({ build }: { build: number }) {
  // Template: T1 — Hero / Statement
  // Beat: <beat label from plan>
  // Builds: <N>
  return (
    <div style={{ width: 1920, height: 1080, background: C.cream, position: 'relative' }}>
      <SlideChrome slideNum={1} totalSlides={<N>} eyebrow="<beat label>" />
      {/* TODO: <content sketch from plan> */}
      <div style={fadeIn(build >= 0)}>{/* element 1 */}</div>
      <div style={fadeIn(build >= 1)}>{/* element 2 */}</div>
    </div>
  );
}

// ... one stub per slide ...

// Main component renders the active slide
export default function Dive() {
  const { slide, build } = useBuild();
  const Slides = [Slide01_..., Slide02_..., /* ... */];
  const Active = Slides[slide];
  return <Active build={build} />;
}
```

For each slide, generate a stub function with:
- A comment block above noting `Template: T## — <name>`, `Beat: <label>`, `Builds: N`, `Content: <sketch>`
- The right `background` (cream or charcoal depending on T1/T23/T8-Dark)
- The right number of `fadeIn(build >= n)` wrappers (one per declared build)
- A leading `// TODO:` line referencing the content sketch — so the user knows what to fill in

### 4. Per-template stub patterns
For known templates, scaffold more than just empty divs. Snippets:

- **T1 / T23 (hero)**: centered display headline placeholder, accent rule, optional supporting line
- **T2 (big-stat)**: 320px Aeonik Mono Bold number + 200px % unit + caption + footer attribution
- **T3 (terminal)**: code-window frame with traffic-light dots, SQL line, result number, wall-time corner
- **T8 (sequential)**: 3 stacked statement divs, third in orange
- **T9 (bullets)**: title + lead + bullets array (mapped from sketch) + KPI strip
- **T15 (chart)**: SVG chart placeholder with axis ticks, reference line, 3 callouts + KPI cards
- **T22 (process)**: 4 stage cards with → arrows between
- **T13 (delta)**: stacked rows with `before → after` value pairs

For unknown templates or templates without a snippet pattern, generate an empty stub with the chrome + the right build wrappers.

### 5. Save and report
Write the `.tsx` file. Report:
- Path written
- Slide count and total build count
- Which slides have full stubs vs. empty stubs
- Suggested next step: "Fill in TODO content, then save to MotherDuck via `mcp__claude_ai_MotherDuck__save_dive`"

## Quality bar

- **Use canonical tokens only.** No `#FF7169`, no `#2D2D2D`. Reference `paper-style-guide`.
- **Match SLIDE_BUILD_COUNTS to the actual `fadeIn` wrappers.** If a slide says `Builds: 3`, the stub must have at least 3 `fadeIn(build >= 0/1/2)` wrappers.
- **Don't generate fake content.** If the plan's content sketch is "76% Easy / 47% Hard", put those literal numbers in. If the sketch is vague, put a `// TODO` and the original sketch as a comment.

## Anti-patterns

- Don't write a complete dive (filling in all content). Skeleton only — the user fills the data.
- Don't invent new template patterns. If the plan uses T11 and you don't have a stub pattern, generate a minimal stub with just the chrome + build wrappers.
- Don't auto-save to MotherDuck. The user runs `save_dive` themselves once content is filled.
- Don't change the `SLIDE_BUILD_COUNTS` from what the plan declared. If the plan has a typo, flag it but use the declared values.
