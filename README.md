# OpenHeritage agent tooling

Public, cross-agent integration files for [OpenHeritage](https://openheritage.online/en/agents), a collaborative genealogy and cultural-heritage platform.

OpenHeritage brings together Ukraine's largest public collection of memorial, grave, and archival document data.

This repository connects compatible AI agents to OpenHeritage in two complementary ways:

- a remote, anonymous, read-only MCP server for live public-record search;
- five portable Agent Skills with domain guidance, safe REST fallbacks, and canonical OpenHeritage links.

No API key is required for public search.

## Ukrainian heritage data at scale

- **Memorials and graves:** discover memorial profiles, grave sites, cemetery records, cemetery photographs, map locations, and transcriptions.
- **Archival documents:** search repositories, sources, digitized documents, page images, XML, transcriptions, and indexed entries with their provenance.

These records are connected through canonical OpenHeritage pages, so agents can move from a discovery lead to the relevant cemetery, memorial, source, or document without treating search results as proof.

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

Add the public OpenHeritage marketplace, then install the complete plugin:

```bash
claude plugin marketplace add OpenHeritageOnline/agent-tooling
claude plugin install agent-tooling@openheritage
```

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

Every Agent Skills-compatible host can also discover the five published skills from the [OpenHeritage Agent Skills index](https://openheritage.online/.well-known/agent-skills/index.json). For an MCP host without plugin support, add the `openheritage` entry from [`.mcp.json`](.mcp.json) to its user or project MCP configuration.

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

[`server.json`](server.json) publishes the remote server as `io.github.OpenHeritageOnline/public-search` in the official MCP Registry. The GitHub Actions workflow publishes it when an `mcp-v*` tag is pushed:

```bash
git tag mcp-v2.9.6
git push origin mcp-v2.9.6
```

The workflow uses GitHub OIDC, so it requires no stored token or domain-verification private key. Registry versions are immutable: bump `server.json` before creating a later tag.

## Safety

- Treat search results as discovery leads, not proof of identity or family relationship.
- Respect record visibility and copyright restrictions.
- Do not crawl, bulk-enumerate, or collect profile/contact data.
- Prefer canonical OpenHeritage pages when sharing results with a user.
- Use authenticated or mutating REST workflows only when the user explicitly requests them.

## Source of truth

The production skill documents are maintained in the main OpenHeritage application repository under `sources/FrontendServer/AgentSkills/`. Keep the copies in `skills/` byte-for-byte synchronized when releasing a new version.
