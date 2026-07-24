# OpenHeritage agent tooling

Public, cross-agent integration files for [OpenHeritage](https://openheritage.online/en/agents), a collaborative genealogy and cultural-heritage platform.

This repository connects compatible AI agents to OpenHeritage in two complementary ways:

- a remote, anonymous, read-only MCP server for live public-record search;
- five portable Agent Skills with domain guidance, safe REST fallbacks, and canonical OpenHeritage links.

No API key is required for public search.

## MCP endpoint

```text
https://openheritage.online/mcp
```

The endpoint uses MCP Streamable HTTP and exposes:

- `search_records`
- `search_memorials`
- `search_cemeteries`
- `search_sources`
- `search_documents`
- `search_repositories`

Use the root [`.mcp.json`](.mcp.json) with clients that support project or plugin MCP configuration.

### Claude Code

Connect only the MCP server:

```bash
claude mcp add --transport http --scope user openheritage https://openheritage.online/mcp
```

To load the complete plugin from a checkout:

```bash
claude --plugin-dir /path/to/agent-tooling
```

The repository includes a Claude Code manifest at [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

### Codex and other Agent Skills clients

Install the portable skills from GitHub with a compatible Agent Skills installer:

```bash
npx skills add OpenHeritageOnline/agent-tooling
```

The repository also includes a Codex manifest at [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json). Plugin-aware hosts can load the repository checkout directly and use its bundled `.mcp.json`.

## Skills

| Skill | Best for |
|---|---|
| `openheritage` | Broad searches across all public OpenHeritage domains |
| `openheritage-archives` | Sources, documents, repositories, collections, files, pages, entries, and exports |
| `openheritage-photos` | Historical photos, media variants, photo maps, corrections, and people on photos |
| `openheritage-memorials` | Memorials, cemeteries, cemetery photos, maps, statistics, and exports |
| `openheritage-researches` | Public genealogy research projects, questions, hypotheses, places, and evidence |

The same versioned skill documents are also published from the OpenHeritage website:

- [Agent Skills discovery index](https://openheritage.online/.well-known/agent-skills/index.json)
- [Umbrella OpenHeritage skill](https://openheritage.online/.well-known/agent-skills/openheritage/SKILL.md)

## MCP Registry

[`server.json`](server.json) is ready for publication to the official MCP Registry:

```bash
mcp-publisher publish
```

Publishing requires the repository owner to authenticate and verify ownership of the `openheritage.online` namespace.

## Safety

- Treat search results as discovery leads, not proof of identity or family relationship.
- Respect record visibility and copyright restrictions.
- Do not crawl, bulk-enumerate, or collect profile/contact data.
- Prefer canonical OpenHeritage pages when sharing results with a user.
- Use authenticated or mutating REST workflows only when the user explicitly requests them.

## Source of truth

The production skill documents are maintained in the main OpenHeritage application repository under `sources/FrontendServer/AgentSkills/`. Keep the copies in `skills/` byte-for-byte synchronized when releasing a new version.
