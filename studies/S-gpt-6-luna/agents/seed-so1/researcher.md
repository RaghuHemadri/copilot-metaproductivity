Improve the agent one step at a time:
1. Read /report/summary.md, then a few files in /report/failures/ to find the most common reason problems are failed.
2. Make one focused change that addresses that reason: edit /agent/solver.md, add a skill under
   /agent/skills/<name>/SKILL.md, or add a helper sub-agent in /agent/subagents.yaml.
3. Run validate() and fix any problems it reports.
4. Finish with the CHANGES and PREDICTED_DELTA lines.
