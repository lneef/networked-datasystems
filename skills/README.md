# Install the KB skill for Codex and Claude Code

Both agents use the same [skill source](consult-networked-data-systems/SKILL.md).
Copy or clone this entire repository to the new machine, then run from its root:

```sh
python3 skills/install.py --dry-run
python3 skills/install.py
```

The installer creates user-wide links at:

- Codex: `~/.agents/skills/consult-networked-data-systems/`
- Claude Code: `~/.claude/skills/consult-networked-data-systems/`

The skill locates the KB through the resolved link, so no username or checkout
path needs editing. Keep the repository at its installed location; both agents
read updates directly from this shared source. Existing conflicting installations
are reported and never overwritten.

Invoke `$consult-networked-data-systems` in Codex or
`/consult-networked-data-systems` in Claude Code. Automatic selection remains
enabled for relevant tasks. Restart the agent if the skill does not appear.
