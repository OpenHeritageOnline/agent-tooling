# OpenHeritage agent tooling

Public, cross-agent integration files for [OpenHeritage](https://openheritage.online/en/agents), a collaborative genealogy and cultural-heritage platform.

OpenHeritage brings together Ukraine's largest public collection of memorial, grave, and archival document data.

This repository connects compatible AI agents to OpenHeritage in three complementary ways:

- a remote, anonymous, read-only MCP server for live public-record search;
- six portable Agent Skills with domain guidance, safe REST fallbacks, and canonical OpenHeritage links;
- a documented Personal API for user-authorized contributions with scoped bearer tokens.

No API key is required for public search.

## Ukrainian heritage data at scale

- **Memorials and graves:** discover memorial profiles, grave sites, cemetery records, cemetery photographs, map locations, and transcriptions.
- **Archival documents:** search repositories and sources, retrieve digitized documents by page or original file, and use XML, transcriptions, parsing, or OCR to answer questions with provenance.

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
- `search_places`
- `search_authors`
- `search_collections`

The MCP server also exposes anonymous, read-only resources for selected public
sources, documents and files, repositories, collections, canonical places,
memorials, cemeteries, and Source classification tags. MCP never accepts a
Personal API token.

Use the root [`.mcp.json`](.mcp.json) with clients that support project or plugin MCP configuration.

## Personal API and newspaper imports

Use the Personal API only for user-authorized contributions:

- interactive reference: `https://openheritage.online/api-docs`;
- OpenAPI 3 document: `https://openheritage.online/api/openapi/v1.json`.

Personal API tokens are bearer tokens and always include `api:read`. A
classified newspaper import additionally uses `api:authors` to create or update
the canonical newspaper organization authority, `api:sources` to create issue
Sources and configure the automated Collection, and `api:documents` to create
the issue document and upload ordered page images and PAGE XML. Send the token
only in the `Authorization: Bearer ...` header, never to MCP or in a URL.

The `openheritage-newspaper-import` skill contains the complete issue workflow.
It resolves the environment-specific UUID for stable Source taxonomy code
`record-kind-newspaper`, creates or reuses the newspaper organization Author,
configures an Author-driven Collection grouped by publication year, records the
holding repository and publication place when known, creates each issue as a
`publication`, and uploads its ordered document pages and PAGE XML. Standalone
newspaper clipping PhotoAssets remain part of `openheritage-photos`.

## Add OpenHeritage to your agent / Додайте OpenHeritage до свого агента

### English

Use the MCP connection for live, public OpenHeritage search. Add the skills as well when you want your agent to receive focused guidance for memorials, graves, archival documents, historical photos, and genealogy research.

**Codex**

```bash
codex mcp add openheritage --url https://openheritage.online/mcp
npx skills add OpenHeritageOnline/agent-tooling
```

**Gemini CLI**

```bash
gemini mcp add --scope user --transport http openheritage https://openheritage.online/mcp
gemini skills install https://github.com/OpenHeritageOnline/agent-tooling
```

**Claude Code** — install the complete plugin, which includes both the MCP server and skills:

```bash
claude plugin marketplace add OpenHeritageOnline/agent-tooling
claude plugin install agent-tooling@openheritage
```

If you only need live search in Claude Code, use this instead:

```bash
claude mcp add --transport http --scope user openheritage https://openheritage.online/mcp
```

Start a new chat after installation. In an open Claude Code session, run `/reload-plugins` after installing the plugin. Do not install both the Claude plugin and its separate MCP entry unless you intentionally want duplicate configuration.

### Українською

Підключіть MCP, щоб агент міг шукати публічні записи OpenHeritage у реальному часі. Додайте також навички, якщо хочете, щоб агент отримав спеціальні інструкції для роботи з меморіалами, могилами, архівними документами, історичними фотографіями та генеалогічними дослідженнями.

**Codex**

```bash
codex mcp add openheritage --url https://openheritage.online/mcp
npx skills add OpenHeritageOnline/agent-tooling
```

**Gemini CLI**

```bash
gemini mcp add --scope user --transport http openheritage https://openheritage.online/mcp
gemini skills install https://github.com/OpenHeritageOnline/agent-tooling
```

**Claude Code** — встановіть повний плагін: він містить і MCP-сервер, і навички.

```bash
claude plugin marketplace add OpenHeritageOnline/agent-tooling
claude plugin install agent-tooling@openheritage
```

Якщо в Claude Code потрібен лише пошук, використайте натомість:

```bash
claude mcp add --transport http --scope user openheritage https://openheritage.online/mcp
```

Після встановлення почніть новий чат. Якщо ви встановили плагін у вже відкритій сесії Claude Code, виконайте `/reload-plugins`. Не встановлюйте одночасно плагін Claude та окремий запис MCP, якщо навмисно не хочете дублювати конфігурацію.

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

Every Agent Skills-compatible host can also discover the six published skills from the [OpenHeritage Agent Skills index](https://openheritage.online/.well-known/agent-skills/index.json). For an MCP host without plugin support, add the `openheritage` entry from [`.mcp.json`](.mcp.json) to its user or project MCP configuration.

## Skills

| Skill | Best for |
|---|---|
| `openheritage` | Broad searches across all public OpenHeritage domains |
| `openheritage-archives` | Sources, documents, repositories, collections, pages, files, entries, and exports |
| `openheritage-newspaper-import` | Complete newspaper issue preparation, organization Authors, automated year Collections, repository and publication-place provenance, ordered page uploads, PAGE XML, verification, and repair |
| `openheritage-photos` | Historical photos, media variants, photo maps, corrections, and people on photos |
| `openheritage-memorials` | Memorials, cemeteries, cemetery photos, maps, statistics, and exports |
| `openheritage-researches` | Public genealogy research projects, questions, hypotheses, places, and evidence |

The same versioned skill documents are also published from the OpenHeritage website:

- [Agent Skills discovery index](https://openheritage.online/.well-known/agent-skills/index.json)
- [Umbrella OpenHeritage skill](https://openheritage.online/.well-known/agent-skills/openheritage/SKILL.md)

## MCP Registry

[`server.json`](server.json) publishes the remote server as `io.github.OpenHeritageOnline/public-search` in the official MCP Registry. The GitHub Actions workflow publishes it when an `mcp-v*` tag is pushed:

```bash
git tag mcp-v2.11.1
git push origin mcp-v2.11.1
```

The workflow uses GitHub OIDC, so it requires no stored token or domain-verification private key. Registry versions are immutable: bump `server.json` before creating a later tag.

Publishing is restricted to protected release refs and the
`mcp-registry-production` GitHub Environment. The publisher is downloaded from
an exact release, verified by SHA256 and Sigstore identity, and checked for the
expected version and source commit before the OIDC-capable job can run. See the
[required repository controls](.github/MCP_PUBLISHING_SECURITY.md) before
creating a release tag.

## Safety

- Treat search results as discovery leads, not proof of identity or family relationship.
- Respect record visibility and copyright restrictions.
- Do not crawl, bulk-enumerate, or collect profile/contact data.
- Prefer canonical OpenHeritage pages when sharing results with a user.
- Use authenticated or mutating REST workflows only when the user explicitly requests them.
- Never print, persist, or forward a Personal API token; request only the scopes needed for the authorized operation.

## Source of truth

The production skill documents are maintained in the main OpenHeritage application repository under `sources/FrontendServer/AgentSkills/`. Keep the copies in `skills/` byte-for-byte synchronized when releasing a new version.
