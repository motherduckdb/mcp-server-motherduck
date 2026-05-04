# Brief — Catalog Context for Agents

*Talk · 25 min · PyData Seattle · audience: ML/data engineers familiar with LLMs*

## Thesis

LLMs write better SQL when the data model itself carries context — column comments, views, and macros — than when given a longer prompt or a bigger model.

## Why this is interesting now

- DABstep benchmark shows pass@1 plateaus at ~76% Easy / ~47% Hard with vanilla prompting + raw tables
- Industry has been chasing prompt engineering and context windows; the underexplored axis is the schema itself
- Spent 8 weeks iterating; the wins came from data-model changes, not model upgrades

## The arc

1. Open with a question the audience can't answer: "your LLM and a senior analyst both miss the same SQL question — why?"
2. Set up DABstep — what it is, why it's hard
3. Show the harness — how we run it (5 tables, prompts, tools)
4. The hard question — show two examples LLMs get wrong on raw schemas
5. Beat 1: column comments — adding them lifts Hard from 47% → 52% with no prompt change
6. Beat 2: views — materialize the messy joins; pass rate climbs again
7. Beat 3: macros — domain idioms baked in
8. Beat 4: iteration — the model learns from the prior trace
9. Scoreboard: V1 → V4 with each iteration's pass rate
10. Closing thesis: the data model IS the context

## Key data points

- DABstep public leaderboard: 76% Easy / 47% Hard baseline (GPT-5)
- After V4 (column comments + views + macros + iteration): 79% Easy / 52% Hard
- Token cost: 3.4K → 3.6K avg (+6%)
- 8 iteration cycles; convergence around iter 6
- 450 questions in benchmark; 5 base tables; 3 metadata files

## Sources

- DABstep paper: https://arxiv.org/abs/2503.12132
- Adyen DABstep blog post
- Internal harness repo: motherduck/dabstep-harness

## Open questions

- Should I show the V3 Twitter detour (where overfitting was visible)? Probably yes — it's a great cautionary beat
- Live demo or recorded? Recorded for safety
- Closing CTA — point at the harness repo or at MotherDuck product?

## Prior work to reference

- 0428-catalog-context-for-agents/ (this project)
- 0205-simple-models-ai-blog/ (related thesis)
