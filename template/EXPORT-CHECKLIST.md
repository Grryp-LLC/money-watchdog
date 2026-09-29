# Publishing notes (Grok Bot template)

1. Create the bot: name `Money Watchdog`, title `Sheriff of your inbox`, avatar hex/yellow, description and system prompt
   from `bot-profile.md`.
2. Add the six skills from `skills/*/SKILL.md`. `getting-started` must be one of the bot's real skills so it gets packed.
3. Add the memories from `memories/profile.md` (one entry per bullet) and `memories/log.md`.
4. Routines are created by `getting-started` in each new owner's timezone. Specs are in `routines/ROUTINES.md`.
5. Plugin: the Gmail marketplace connector only (read-only use). No custom MCP servers.
6. Pack with gettingStarted = `getting-started`, using `template/template-manifest.json` as the source.
7. The poster kit install URL is pinned to a commit in `memories/profile.md` (`poster_kit_url`).

Never included: real inbox data, personal names, email addresses, account or card numbers, tokens.
