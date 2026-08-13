# Licensing and provenance

For every third-party or GitHub input, record repository URL, exact file/path, version or commit, license name and link, copyright holder, whether content or only an idea is used, modifications, distribution target and required notices.

Rules:

1. Check the license at the exact file/resource scope; a repository may give different Skills or docs different licenses.
2. Do not copy code, prompts, examples, datasets, icons or workbook templates when the license is absent, unclear or incompatible.
3. General architecture ideas may be independently implemented without copying protected expression. Document the source as design inspiration.
4. Preserve attribution and license text when required. Do not imply endorsement or use third-party trademarks as product branding.
5. Never upload proprietary drawings, company prices, keys or internal prompts to public services while researching.

Useful official references for architecture review:

- OpenAI Skills/Plugins: progressive disclosure and resource folders. Verify each individual Skill license.
- Microsoft AutoGen: layered agents/extensions/runtime; docs CC BY 4.0 and code MIT in its repository.
- LangGraph Supervisor: central supervisor and explicit handoff; MIT repository.

This list is not a dependency recommendation and not legal advice. Prefer no third-party runtime dependency unless it materially improves the product and its maintenance/security cost is accepted.
