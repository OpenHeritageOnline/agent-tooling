# MCP publishing security controls

The workflow in `workflows/publish-mcp-registry.yml` fails closed unless it is
running in `OpenHeritageOnline/agent-tooling` from a protected `mcp-v*` tag or,
for an explicitly dispatched run, protected branch `main`.

The repository file alone cannot create GitHub rulesets, Environment reviewers,
or organization policies. Repository and organization administrators must keep
the following controls enabled.

## Required GitHub configuration

1. Create an active tag ruleset targeting `mcp-v*`.
   - Restrict tag creation to the release maintainers.
   - Restrict tag updates and deletions, with the smallest practical bypass
     list.
2. Protect `main` with an active branch ruleset or branch protection rule.
3. Create the `mcp-registry-production` Environment used by the workflow.
   - Add at least one required reviewer.
   - Enable **Prevent self-review**.
   - Disable administrator bypass.
   - Select only the `mcp-v*` tag pattern and `main` branch as deployment
     branches and tags.
4. At organization level, enable **Require actions to be pinned to a
   full-length commit SHA** under GitHub Actions policies.
5. Keep Dependabot version updates enabled. `.github/dependabot.yml` updates
   GitHub Actions weekly; review the upstream release and diff before merging.

`github.ref_protected` is checked before any publisher download or OIDC-capable
job. A missing matching ruleset therefore prevents publishing.

## Updating `mcp-publisher`

Never replace the versioned release URL with `releases/latest`. Update all of
these workflow values together in one reviewed pull request:

- `MCP_PUBLISHER_VERSION`;
- `MCP_PUBLISHER_RELEASE_COMMIT`;
- `MCP_PUBLISHER_ASSET_SHA256`;
- `MCP_PUBLISHER_BUNDLE_SHA256`;
- `MCP_PUBLISHER_BINARY_SHA256`;
- `MCP_PUBLISHER_SIGSTORE_IDENTITY`;
- the artifact name in both artifact steps.

Take the archive and Sigstore bundle checksums from the exact upstream release.
Derive the binary checksum only after the archive checksum and Sigstore identity
have both been verified. The expected certificate identity must identify the
upstream release workflow at the exact version tag, and the CLI `--version`
output must contain both the expected version and release commit.

Do not approve the `mcp-registry-production` deployment until the unprivileged
`Verify release source and publisher` job has passed and the proposed
`server.json` version has been reviewed.
