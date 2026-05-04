---
name: motherduck-design-system
description: Design system reference for the MotherDuck marketing website (packages/mkt, packages/ui, packages/quackbot) — fonts, colors, spacing, borders, shadows, buttons, inputs, and dark sections. Use when building or editing any web page, section, card, button, or component; when choosing fonts/colors/spacing/shadows; when reviewing styled-components or Tailwind styling; or when answering design-language questions about motherduck.com.
---

# MotherDuck Website — Design System

## When to use

Invoke this skill when:
- Building or editing a page, section, card, button, form, tag, or any visual component in `packages/mkt`, `packages/ui`, or `packages/quackbot`
- Choosing fonts, colors, spacing, radii, borders, shadows, or animations
- Reviewing a PR that touches styled-components or Tailwind classes
- Answering questions about MotherDuck's visual language or brand feel

Complement — don't replace — `.claude/rules/font-usage.md` and `.claude/rules/color-usage.md`. Those are the canonical rule files; this skill adds the observed conventions and concrete values.

## Canonical source files

- **Theme tokens** (colors + breakpoints, the only defined tokens): `packages/ui/theme/index.ts`
- **Global reset + `h1Styles`…`h6Styles` + markdown scale**: `packages/ui/global-style.tsx`
- **Primitives**: `packages/ui/button.tsx`, `link.tsx`, `input.tsx`, `checkbox.tsx`, `modal.tsx`, `text-body.tsx`
- **Fonts**: `packages/mkt/fonts.css` (Pages Router) + `packages/mkt/globals.css` (App Router)
- **Tailwind**: `packages/mkt/tailwind.config.ts` (colors + screens + fonts; NO spacing/radius/shadow extensions)
- **Default container**: `packages/mkt/components/common/container.tsx`
- **Section-bg variant palette**: `packages/mkt/components/landing-page-2/lp2-section-wrapper.tsx`

Styling is overwhelmingly **styled-components** in `packages/mkt`. Tailwind is used for layout utilities only — colors/radii/shadows go through styled-components + `theme.colors`.

## Typography

### Fonts
| Font | Role | Weights loaded | Rules |
|---|---|---|---|
| **Aeonik Mono** | Titles, headings (h1–h6), tags, eyebrows | 400 (woff2), 700 (otf — App Router only) | **Always UPPERCASE** |
| **Inter** | Everything else (body, buttons, nav, forms) | 300, 400, 600, 700 | Normal case (buttons apply uppercase at component level) |
| **Aeonik Fono** | ⚠️ DEPRECATED — still in ~20 files | — | Do not use in new code; replace with Aeonik Mono or Inter |

Never use weights outside the loaded set — synthetic fallback looks wrong.

### Heading scale (from `h1Styles`…`h6Styles`)
| Tag | Mobile | sm (728) | md (960) | line-height |
|---|---|---|---|---|
| h1 | 30 | 56 | 80 | 140% → 120% |
| h2 | 24 | 32 | 40 | 140% → 120% |
| h3 | 24 | — | 32 | 140% |
| h4 | 18 | 24 | 32 | 140% |
| h5 | 18 | — | 24 | 140% |
| h6 | 18 | — | — | 140% |

All headings: weight 400, Aeonik Mono, UPPERCASE (applied globally via `titleStyles`). **Import the `hXStyles` mixins from `@motherduck/ui`** rather than hand-rolling the responsive scale.

### Body defaults (global `p`)
```
Inter, weight 300, 16px, line-height 140–160%, letter-spacing 0.02em
```
Use `<TextBody xs='16px' sm='18px' fontWeight='300' lineHeight='160%'>` for parametric responsive body text (accepts `xs`/`sm`/`md`/`lg`/`xl` in px).

### Buttons (text)
Inter 400, 16px, 120% line-height, UPPERCASE (14px on `sm-*` variants). `duckdb-*` variants keep mixed case.

### Links
- Default anchor: `color: theme.colors.black`, `text-underline-offset: 0.22em`
- Markdown links: Inter 700, underlined
- **Hover → `theme.colors.sky` (#6FC2FF)** — universal interactive-hover color
- "Learn more" pattern: `<Button variant='underline' icon='right-arrow'>` (UPPERCASE)

### Letter-spacing
- `0.02em` for Inter body and most titles
- `normal` (explicitly override the 0.02em default) when applying Aeonik Mono to paragraph-like text

## Colors

### Full palette (30 tokens in `theme.colors`)

**Neutrals** — `white #FFFFFF`, `deepBlack #000` (unused), `snow #F8F8F7`, `darkSnow #ECE5DD`, `sand #F4EFEA`, `sandGrey #ECE6DF`, `darkSand #E1D6CB`, `lighterGrey #D7D7D7`, `lightGrey #C0C0C0`, `grey #A1A1A1`, `darkGrey #818181`, `darkerGrey #666666`, **`black #383838`** (warm near-black — the real default "black")

**Sky / blue** — `lightestSky #CEEBFF`, `lightSky #97D4FF`, `sky #6FC2FF`, `darkSky #2BA5FF`, `darkerSky #1276BF`
**Garden / teal** — `lighterGarden #53DBC9`, `lightGarden #50C7B7`, `garden #16AA98`, `darkGarden #068475`
**Sun / yellow** — `lighterSun #FAF175`, `lightSun #F9EE3E`, `sun #FFDE00`
**Watermelon / coral** — `lightWatermelon #FF9A94`, `watermelon #FF7169`, `darkWatermelon #E23F35`
**Duck / brand orange** — `lighterDuck #FFDCBD`, `lightDuck #FFC18A`, `duck #FF9538`

### Load-bearing rules
1. **Never introduce hex/rgb/hsl literals in new code.** Use `theme.colors.<token>`. If nothing fits, ask before adding a token to `packages/ui/theme/index.ts`.
2. **`theme.colors.black` = `#383838`, not pure black.** It's THE default for borders, text, dark-section backgrounds, icon fills. `deepBlack #000` exists but is essentially unused — don't reach for it.
3. **Canonical section-background palette** (from `lp2-section-wrapper.tsx`): `sand`, `black`, `white`, `sun`, `sky`, `garden`.
4. **Page default bg**: `sand` (#F4EFEA), set on `<html class='bg-sand'>` in `packages/mkt/app/layout.tsx`.

### Semantic conventions
| Intent | Token |
|---|---|
| Body text on light bg | `theme.colors.black` (#383838) |
| Body text on dark bg | `white` or `snow` |
| Muted / secondary text | `darkGrey` |
| Disabled text/icons | `grey` |
| Default border (cards, buttons, inputs, images) | `black` @ 2px |
| Soft border on warm surfaces | `darkSand` |
| Table row dividers | `darkSnow` |
| Hairline dividers on white | `lightGrey` or `${black}26` |
| Primary CTA bg | `sky` → `darkSky` on active |
| Secondary CTA bg | `sand` → `darkSand` on active |
| Brand accent | `duck` (+ `${duck}AA` overlay is very common) |
| Validation success | `darkGarden` |
| Validation error | `darkWatermelon` |
| Focus ring | `darkSky` |

### Content-type tag colors (`common/card-type-tag.tsx`)
`news → lightSun` · `article → lightSky` · `video → lightGarden` · `podcast → watermelon` · `case-study → lightWatermelon`.

### Transparency — prefer hex-alpha suffix over `rgba()`
```tsx
background: ${({ theme }) => theme.colors.black}26;   // ~15% alpha
overlay:    ${({ theme }) => theme.colors.duck}AA;    // ~67% — the common brand overlay
```
Common suffixes: `08`≈3% · `14`≈8% · `1A`=10% · `26`≈15% · `32`≈20% · `50`≈31% · `66`=40% · `99`=60% · `AA`≈67% · `CC`=80%.

### Dark sections
**There is no dark mode.** Dark UI is per-section: set `background: theme.colors.black`, `color: white/snow`, swap `<Button variant='underline'>` → `'underline-white'`, and use `*-white.svg` icon variants. The footer is permanently dark.

## Spacing

### Breakpoints (Tailwind + styled-components, identical)
```
xs 556  ·  sm 728  ·  md 960  ·  lg 1302  ·  xl 1600
```
Use `SM_MIN_MEDIA_QUERY`, `MD_MIN_MEDIA_QUERY`, `LG_MIN_MEDIA_QUERY` from `@motherduck/ui/theme`. **Mobile-first.**

### Grid rhythm
**Loose base-4 for small values, page-specific for large.** Small spacing cleanly hits 4/8/12/16/20/24/32/40; section paddings drift off-grid (e.g. `92`, `114`, `144`). Match neighbors rather than forcing a scale. Button paddings include half-pixels (`16.5 × 22`) — intentional height-tuning, leave as-is.

### Common values (sampled across ~140 components)
| Purpose | Values |
|---|---|
| Flex/grid gap | `24`, `32` most common; then `16`, `12`, `8`, `40`, `48`, `64` |
| Card internal padding | `24` mobile → `32` desktop |
| Small pill/tag padding | `8px 16px`, `6px 12px`, `4px 8px` |
| Button padding | `16.5px 22px` (default), `13.5px 20px` (sm) |
| Input padding | `16px 40px 16px 24px` |
| Section vertical padding (ladder) | mobile 40–64 → sm 64–100 → md 80–120 → lg 100–160 |
| Section horizontal gutter | `24` mobile, `20` sm/md, `30` lg (from `Container`) |

### Widths
- Default `<Container>` caps at **1302px**; `removePadding` wide variant caps at **1440px**
- Comfortable reading column: **1028px** recurs as a de-facto max for long copy
- Narrow text columns: 400–500 (hero copy), 600–700 (paragraphs)

### Radii
| Value | Use |
|---|---|
| **`2px`** | **Default everywhere** — buttons, inputs, checkboxes, cards, modals, tags, filter pills, video embeds |
| `50%` | Circles (avatars, bullet dots, social icons) |
| `3px` | Inline `code` backgrounds |
| `100px` | Toggle switches only |
| `10–20px` | Soft sub-system on humandb, hypertenancy, dives pages |

**Sharp corners are part of the brand. Don't default to rounded cards.**

### Critical fixed heights
- Header: `--header-mobile: 70px` / `--header-desktop: 90px`
- Eyebrow: `--eyebrow-mobile: 70px` / `--eyebrow-desktop: 55px`
- Input max-height: `58px`; checkbox: `18×18px`

## Borders & shadows (the two signatures)

### Borders
`border: 2px solid ${theme.colors.black}` is on **nearly every card, button, input, modal, and markdown `<img>`**. This is THE defining visual. Keep it for new components. No dashed borders anywhere; dotted only on tooltip-trigger text-decoration.

### Shadows — the hard-offset "sticker" shadow
Zero blur, `theme.colors.black`, going down-and-left:
```css
box-shadow: -4px 4px 0px 0px ${theme.colors.black};   /* mobile */
box-shadow: -6px 6px 0px 0px ${theme.colors.black};   /* sm / md */
box-shadow: -8px 8px 0px 0px ${theme.colors.black};   /* lg */
```
Scales responsively, up to `-12/-16` on large heroes.

**Alternate idiom** — a sibling `StyledWrapper` div with `background: black` sits beneath the card; the card hovers to `translate(7px, -7px)` (buttons) or `translate(14px, -14px)` (cards) and reveals the black beneath as the "shadow." Both patterns coexist.

Soft blurred shadows are rare — reserved for dropdown overlays (`0px 4px 8px rgba(0,0,0,0.1)`).

## Transitions & animations

- **Default hover**: `transition: transform 120ms ease-in-out`
- Other durations: `125–150ms` (micro-fades), `200ms` (bg/border), `300–500ms` (accordion)
- **Easing**: `ease-in-out` is the overwhelming default
- **Libraries**: `gsap` + `ScrollTrigger` for scroll-linked, `lottie-react` for JSON, `swiper` for carousels. **No framer-motion, no react-spring** — do not add.
- **Link hover**: text + underline cross-fade to `theme.colors.sky`

## Primitives

### Button variants (`packages/ui/button.tsx`)
All: 2px black border, 2px radius, Inter 16/400/120%, UPPERCASE, lift-and-shadow on hover.
- `primary` — bg `sky`, active `darkSky`
- `secondary` — bg `sand`, active `darkSand`
- `sm-primary` / `sm-secondary` — smaller padding, 14px font
- `underline` — text-only, 0.09em underline, hover → `sky`
- `underline-white` — underline variant for dark backgrounds
- `duckdb-primary` / `duckdb-secondary` — keeps mixed case, mobile-up padding

Icon slots: 20×20 default, 24×24 for Google/GitHub logos. Always build CTAs via `<Button>`.

### Inputs (`packages/ui/input.tsx`)
```
bg:      rgba(248,248,247,0.7)        /* 70% snow */
border:  2px solid black              /* hover/focus → darkSky
                                         valid       → darkGarden
                                         error       → darkWatermelon */
radius:  2px
padding: 16px 40px 16px 24px
font:    Inter 400 / 16px / 160% / 0.02em
```
Floating label animates top-left on value; valid/invalid icon at `right: 17px`.

### Cards (canonical anatomy)
```
border: 2px solid ${theme.colors.black};
border-radius: 2px;
background: white;                             // or snow / sand
padding: 24px;                                 // → 32px at MD_MIN_MEDIA_QUERY
transition: transform 120ms ease-in-out;
// Hover: translate(14px, -14px) with black sibling-wrapper
//        OR box-shadow: -6px 6px 0px 0px ${theme.colors.black}
```

### Tags / pills / eyebrows
```
font-family: 'Aeonik Mono';
font-size: 12px;
line-height: 140%;
text-transform: uppercase;
padding: 10px 12px;                            // or 6–12 vert × 16–24 horiz
background: ${theme.colors.darkSnow};          // or lightDuck, lightSun, sun, etc.
border-radius: 2px;                            // NEVER full-pill shape
```

## Icons

No icon library is installed (no lucide-react, no heroicons, no react-icons). All icons are project-owned SVGs loaded via `@svgr/webpack` from:
- `packages/ui/assets/icons/` — core button icons
- `packages/mkt/assets/icons/` — decorative + content-type + brand icons (100+ `misc-*.svg`)

Default sizes: 20×20 (button), 24×24 (header/footer/input-leading/card-arrow). Dark-mode icons use explicit `*-white.svg` duplicates — not `currentColor`.

## Images & media

- `next/image` with the `fill` pattern inside `position: relative` + `aspect-ratio: 16/9`
- Markdown `<img>` auto-gets the 2px black border
- Avatars: `border-radius: 50%`; everything else: sharp corners

## Decorative motifs

- **Noise-gradient backgrounds**: `background-image: url('/images/noise-bg-dual-gradient.png'); background-size: 250px;` — used on heroes and the header
- **Edge-fade gradients** on horizontal scrollers: `linear-gradient(90deg, ${theme.colors.sand} 0%, ${theme.colors.sand}00 100%)`
- **Decorative SVG shapes** (`misc-*.svg`): clouds, triangles, stars, cylinders, polygons, hearts, clips — positioned absolutely behind content
- **Duck iconography**: `misc-duck-sticker.svg`, `misc-duck-squares.svg`, `misc-duckdb-certified.svg`, wordmark/mono logos

## Commit conventions

From `.claude/rules/commit-rules.md`:
```
<type>: <taskId> <subject>        # type ∈ {feat, fix, docs, refactor}
```
Task IDs: `MDCK-…`, `CU-…`, `SMD…`, or literal words `staging`, `hotfix`, `maintenance`. Small copy/tooltip/content changes use `fix:` with `(SMD)`. Prefer `pnpm run commit` (commitizen). Never `--no-verify`.

## Anti-patterns (don't copy these from the codebase)

Observed violations that exist but shouldn't propagate:
- Raw hex/rgb literals in `humandb-page/hero-section.tsx` (bright greens `rgba(74,222,128,…)`)
- Raw hex in `instant-sql-page/results-card.tsx` (`#ff3870`, `#ffbe19`)
- Hard-coded `#e1d6cb` instead of `${theme.colors.darkSand}` in `product-feature-grid-section.tsx`
- Hard-coded `#383838` in `box-shadow` instead of `${theme.colors.black}` on several hero sections
- `tailwind.config.ts` has `darkSnow: ' #ECE5DD'` with a leading space (broken); also missing 7 tokens (`darkerGrey`, `lightestSky`, `darkerSky`, `lighterGarden`, `lighterSun`, `lightDuck`, `lighterDuck`). Don't reach for those in Tailwind — use styled-components.

## Quick-start cheat sheet

```tsx
import styled from 'styled-components';
import { h2Styles, SM_MIN_MEDIA_QUERY, MD_MIN_MEDIA_QUERY } from '@motherduck/ui/theme';
import { Button } from '@motherduck/ui/button';
import { TextBody } from '@motherduck/ui/text-body';

const Section = styled.section`
  background: ${({ theme }) => theme.colors.sand};
  padding: 64px 24px;
  ${SM_MIN_MEDIA_QUERY} { padding: 80px 20px; }
  ${MD_MIN_MEDIA_QUERY} { padding: 120px 20px; }
`;

const Heading = styled.h2`
  ${h2Styles}
  letter-spacing: 0.02em;
`;

const Tag = styled.span`
  font-family: 'Aeonik Mono';
  font-size: 12px;
  text-transform: uppercase;
  padding: 10px 12px;
  background: ${({ theme }) => theme.colors.darkSnow};
  border-radius: 2px;
  width: fit-content;
`;

const Card = styled.div`
  border: 2px solid ${({ theme }) => theme.colors.black};
  border-radius: 2px;
  background: ${({ theme }) => theme.colors.white};
  padding: 24px;
  transition: transform 120ms ease-in-out;
  box-shadow: -4px 4px 0px 0px ${({ theme }) => theme.colors.black};
  ${MD_MIN_MEDIA_QUERY} {
    padding: 32px;
    box-shadow: -6px 6px 0px 0px ${({ theme }) => theme.colors.black};
  }
`;

// Usage
<Section>
  <Tag>New Feature</Tag>
  <Heading>Ship fast with DuckDB in the cloud</Heading>
  <TextBody xs='16px' sm='18px' lineHeight='160%'>
    MotherDuck pairs the speed of DuckDB with the ergonomics of a managed service.
  </TextBody>
  <Button variant='primary' icon='right-arrow'>Get started</Button>
</Section>
```
