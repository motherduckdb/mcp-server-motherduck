# motherduck-narrative

A Claude Code plugin that bundles the agents and skills for MotherDuck DevRel's slide / Dive / talk authoring workflow.

## What's inside

### Skills

| Skill | Invocation | Purpose |
|---|---|---|
| `paper-style-guide` | both | Canonical design tokens + 24-template catalog for the Paper slide library. Auto-pulled when generating Dives or editing Paper. |
| `slide-plan` | user-only (`/slide-plan`) | Brief → `slide-plan.md` with template assignments + `SLIDE_BUILD_COUNTS` array. |
| `paper-from-plan` | user-only (`/paper-from-plan`) | `slide-plan.md` → Paper artboards (one per slide), cloned from the template library and stamped with content sketches. |
| `paper-to-dive` | user-only (`/paper-to-dive`) | Finished Paper artboards → `dive.tsx` with slide navigation, build counter, fadeIn wrappers, and per-slide JSX extracted from Paper. |
| `motherduck-design-system` | both | MotherDuck marketing-website design system (fonts, colors, spacing, primitives) — distinct from the slide template tokens. |
| `humanizer` | both | Remove signs of AI-generated writing — em-dash overuse, rule-of-three, inflated symbolism, vague attributions, negative parallelisms. Use as a final prose pass on drafts. |

### Subagents

| Agent | Use when |
|---|---|
| `narrative-arc-reviewer` | A brief / slide-plan / script / Dive is ready for a structural pass. Read-only. Returns a slide-level punch list + arc diagram + top-3 fixes. |
| `paper-cohesion-auditor` | The Paper template library has had multiple authors / agents touch it. Detects token drift, header collisions, footer drift, font leaks. Reports or fixes. |

## Install

### Option A — install from the `mcp-server-motherduck` marketplace

```
/plugin marketplace add motherduckdb/mcp-server-motherduck
/plugin install motherduck-narrative@motherduck-devrel
```

For local development, point at your clone instead:

```
/plugin marketplace add ~/code/mcp-server-motherduck
/plugin install motherduck-narrative@motherduck-devrel
```

### Option B — symlink for active iteration

While editing the plugin itself, symlink it into your project's `.claude/` so changes are picked up without reinstalling:

```bash
cd /path/to/your/project
ln -s ~/code/mcp-server-motherduck/plugins/motherduck-narrative/skills .claude/skills-narrative
ln -s ~/code/mcp-server-motherduck/plugins/motherduck-narrative/agents .claude/agents-narrative
```

## Workflow

See **[WORKFLOW.md](./WORKFLOW.md)** for a detailed walkthrough of each stage. Visual flow chart in the team Paper file (`Slide Deck Template` → `Workflow chart — narrative plugin` artboard).

The skills chain naturally:

```
1. Draft brief.md
2. /slide-plan projects/<slug>                  → slide-plan.md
3. (recommended) narrative-arc-reviewer subagent on slide-plan.md
4. /paper-from-plan projects/<slug>             → Paper artboards (one per slide)
5. Pixel-perfect manual edits in Paper
6. (recommended) paper-cohesion-auditor subagent
7. /paper-to-dive projects/<slug>               → dive.tsx with slide nav + build counter
8. Fill any text + humanizer (prose pass)
9. Iterate: layer in MotherDuck-loaded charts via Recharts (optional)
10. Save to MotherDuck via mcp__claude_ai_MotherDuck__save_dive
```

`paper-style-guide` and `motherduck-design-system` are reference skills — they get pulled into context whenever you're touching slides, Dives, or website code, so you stop drifting tokens.

## Iterate

This plugin is meant to evolve as the MotherDuck content workflow matures. To propose changes:

1. Branch off `main` of `mcp-server-motherduck`
2. Edit a skill or agent markdown file under `plugins/motherduck-narrative/`
3. Test against a real project (`/reload-plugins` to pick up changes)
4. Open a PR
5. Teammates `/plugin update motherduck-narrative` once merged

Treat the prompts inside skills/agents as production prompts: small, deliberate edits with clear motivation in commit messages.

## Conventions encoded here

- **Canonical Paper tokens**: cream `#F4EFEA`, charcoal `#383838`, MotherDuck duck orange `#FF9538`, muted `#888888`. No coral `#FF7169`. No pure black `#000`. See `skills/paper-style-guide/SKILL.md`.
- **Build-step annotations**: every multi-state slide carries `▸ N` markers in 11px `#B8B0A4`. The Dive's `SLIDE_BUILD_COUNTS` matches.
- **Placeholder convention**: `[BRACKETED]` not `{{mustache}}`. `NN / NN` for page counters.
- **Templates over invention**: 24 catalogued templates (T1–T23 + T8-Dark). T12/T14 skipped — bespoke. Don't invent T24.
