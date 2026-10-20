Improve the agent one step at a time, like a careful researcher:
1. Read /report/summary.md, then a few files in /report/failures/ to find the most common reason problems are failed.
   Prefer reasons that recur across several problems over the details of a single problem.
2. Make one focused, general change that addresses that reason: edit /agent/solver.md, add or edit a skill under
   /agent/skills/<name>/SKILL.md, or add a helper sub-agent in /agent/subagents.yaml.
3. Simplicity criterion: all else being equal, simpler is better. A small gain that adds a lot of text is not worth it.
   Removing text, rules or skills that do not clearly help, at equal performance, is a win: check whether existing
   instructions or skills are redundant, over-specific (written for one problem) or contradictory, and delete them.
   Never add content that is specific to a single problem.
4. Do not break what works: problems that pass now must keep passing. Rigid rules (ALWAYS / NEVER) are risky; use them
   only for things that hold for every problem.
5. Run validate() and fix any problems it reports.
6. Finish with the CHANGES and PREDICTED_DELTA lines.
