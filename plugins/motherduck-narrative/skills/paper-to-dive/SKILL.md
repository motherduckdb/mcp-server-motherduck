---
name: paper-to-dive
description: Convert a column of finished Paper artboards into a working `dive.tsx` — one slide function per artboard, with slide-navigation wiring (advance/back, keyboard arrows), build-step counter, fadeIn helper, and `SLIDE_BUILD_COUNTS` array. Use after manual pixel-perfect Paper edits and before saving the Dive to MotherDuck. Pulls Paper JSX via `get_jsx` and rewrites it into Dive-shaped React.
disable-model-invocation: true
---

# paper-to-dive

Take a finished column of Paper artboards (the visual source of truth for a talk/Dive) and produce a working `dive.tsx` file: per-slide functions extracted from the Paper JSX, slide navigation, build-step counter, fadeIn helper, and the build-counts array.

After this skill runs, the Dive is wired and renderable. You may still want to layer in MotherDuck-loaded charts (Recharts) for live data — that's a manual iteration on top.

## Inputs

```
/paper-to-dive projects/<slug>/slide-plan.md
/paper-to-dive projects/<slug>/slide-plan.md --paper-file "Talk Title"
```

The slide-plan provides slide order, beat labels, and `SLIDE_BUILD_COUNTS`. The Paper file provides the visual content. Both are required.

## Workflow

### 1. Load context
- Call `mcp__plugin_paper-desktop_paper__get_guide({ topic: "paper-mcp-instructions" })` once.
- Read `slide-plan.md`. Extract the slide order, beat labels, and `SLIDE_BUILD_COUNTS`.
- Pull canonical tokens from `paper-style-guide`.

### 2. Locate the talk's Paper artboards
- `get_basic_info` to enumerate artboards.
- Match artboards named `Slide N · <beat label>` to slide-plan entries by slide number.
- If any plan entry has no matching artboard, flag and stop — don't make up content.

### 3. Per slide, extract JSX
For each artboard:
1. `get_jsx({ nodeId, format: "inline-styles" })`
2. Wrap the result in a `Slide<NN>_<KebabName>({ build }: { build: number })` function.
3. Wire build-step `fadeIn` calls:
   - The plan declares `Builds: N` for this slide.
   - Identify revealable groups in the JSX (the design's `▸ N` markers and the slide's natural element groups).
   - Wrap each in `<div style={fadeIn(build >= n)}>`.
   - Strip the `▸ N` build-marker text nodes from the output (those are authoring metadata, not deck content).
4. Replace any literal hex tokens with the canonical `C` constants object (see template below).

### 4. Generate the dive.tsx file

```tsx
// <Talk title from slide-plan H1>
// Generated <date> · <N> slides · <total> build steps

import React, { useState, useEffect, useCallback } from "react";

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

const SLIDE_BUILD_COUNTS = [/* from slide-plan */];

const fadeIn = (visible: boolean): React.CSSProperties => ({
  opacity: visible ? 1 : 0,
  transition: "opacity 0.4s ease",
});

// Slide / build controller — keyboard arrows + click
function useSlideNav() {
  const [slide, setSlide] = useState(0);
  const [build, setBuild] = useState(0);

  const advance = useCallback(() => {
    const max = SLIDE_BUILD_COUNTS[slide] || 1;
    if (build < max - 1) setBuild((b) => b + 1);
    else if (slide < SLIDE_BUILD_COUNTS.length - 1) {
      setSlide((s) => s + 1);
      setBuild(0);
    }
  }, [slide, build]);

  const back = useCallback(() => {
    if (build > 0) setBuild((b) => b - 1);
    else if (slide > 0) {
      const prev = slide - 1;
      setSlide(prev);
      setBuild(SLIDE_BUILD_COUNTS[prev] - 1);
    }
  }, [slide, build]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); advance(); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); back(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [advance, back]);

  return { slide, build, advance, back };
}

// One function per slide — JSX extracted from Paper artboard
function Slide01_<Name>({ build }: { build: number }) {
  return (
    <div style={{ /* extracted from get_jsx */ }}>
      {/* fadeIn wrappers replacing build markers */}
    </div>
  );
}

// ... rest of slide functions ...

export default function Dive() {
  const { slide, build, advance } = useSlideNav();
  const Slides = [Slide01_..., Slide02_..., /* ... */];
  const Active = Slides[slide];
  return (
    <div onClick={advance} style={{ cursor: "pointer", width: 1920, height: 1080 }}>
      <Active build={build} />
    </div>
  );
}
```

### 5. Save and report
Write to `<project-dir>/dive.tsx`. Report:
- Path written
- Slide count + total build count
- Slides whose `▸ N` markers didn't match the declared build count (so the user knows where to verify wiring)
- Suggested next step: `mcp__claude_ai_MotherDuck__save_dive` once content checks pass; or, for live data, layer in Recharts components that pull from MotherDuck.

## Quality bar

- **Strip `▸ N` build markers from the output.** They're authoring metadata. Replace each with the matching `fadeIn(build >= n)` wrapper around its sibling group.
- **Use the `C` constants, not literal hexes.** Convert any `#FF9538` / `#383838` / `#F4EFEA` etc. in the extracted JSX to `C.orange` / `C.charcoal` / `C.cream`. Drift-prevention.
- **Match `SLIDE_BUILD_COUNTS` to actual `fadeIn` wrappers.** If a slide says builds: 3 but you generated 4 wrappers, fix the wrappers before writing.
- **Don't auto-save to MotherDuck.** The user runs `save_dive` themselves.

## Anti-patterns

- Don't fabricate content. If a Paper artboard is missing for a slide-plan entry, stop and report.
- Don't add styling beyond what Paper produced. The Paper file is the visual source of truth — Dive renders it.
- Don't wire data fetching here. Recharts/MotherDuck data is a separate iteration after this skill writes the static skeleton.
- Don't introduce React state beyond `useSlideNav`. Keep it simple.

## Iteration: live charts

Once `dive.tsx` is generated and saved as a static Dive, you may want one or more slides to load live data from MotherDuck and render via Recharts. That's a manual iteration:

1. Pick a slide that should be live (e.g., the leaderboard, the per-iteration line chart).
2. Add a `useEffect` that calls `mcp__claude_ai_MotherDuck__query` against your dataset.
3. Replace the static SVG/inline data with a Recharts component (`<LineChart>`, `<BarChart>`, etc.) consuming the query result.
4. Re-save the Dive.

Don't try to make this skill do data wiring — it's per-slide and per-talk specific.
