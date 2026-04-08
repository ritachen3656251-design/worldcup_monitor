# WorldCup Monitor Constitution

<!--
Sync Impact Report:
- Version change: [TEMPLATE] → 1.0.0
- Modified principles: All 9 principles defined from template placeholders
- Added sections: Core Principles (9), Technical Standards, Development Workflow, Governance
- Removed sections: None (template placeholders replaced)
- Templates requiring updates:
  ✅ constitution.md (this file)
  ✅ plan-template.md (updated with constitution checks for all 9 principles)
  ✅ spec-template.md (updated with constitution alignment section)
  ✅ tasks-template.md (updated with constitution-driven infrastructure tasks)
- Follow-up TODOs: None - all templates synchronized
-->

## Core Principles

### I. Product Positioning: AI Editorial Department

This is an "AI Editorial Department," not a content aggregator. Every piece of information presented to users MUST be AI-processed output, never raw content forwarding. Product taste and editorial judgment are the highest priority.

**Rationale**: Differentiation through curation and intelligence, not volume. Users trust the system to filter and synthesize, not to dump raw feeds.

### II. Data Honesty

AI-generated content MUST NOT introduce facts absent from source material. Every factual claim MUST be traceable to original sources. Credibility classification (Verified / Pending / Rumor) MUST accompany all content displays.

**Rationale**: Trust is the product's foundation. Hallucinations or unsourced claims destroy credibility irreversibly.

### III. Defensive Engineering (NON-NEGOTIABLE)

- All LLM output parsing MUST be wrapped in try-except blocks; parse failures log and skip, never crash
- `json.loads()` without exception handling is FORBIDDEN
- LLM input MUST be truncated (max 1500 characters for article bodies)
- API daily call counter with hard limits MUST be implemented to prevent runaway costs
- Every pipeline stage MUST log input/output counts

**Rationale**: LLMs are unreliable parsers. Cost overruns from infinite loops are unacceptable. Observability prevents silent failures.

### IV. Configuration Externalization

All tunable parameters MUST live in configuration files, never hardcoded:
- Scraping intervals
- Hotness thresholds
- Push notification thresholds
- API call limits
- Clustering similarity thresholds

**Rationale**: Rapid iteration without code changes. Environment-specific tuning. Prevents magic numbers scattered across codebase.

### V. Prompt-Code Separation

All prompt templates MUST reside in dedicated directory (e.g., `prompts/`). Code MUST load prompts from files at runtime. Hardcoded prompts in functions are FORBIDDEN.

**Rationale**: Prompt engineering is iterative. Non-engineers should be able to refine prompts. Version control for prompt evolution.

### VI. Crawler Standards

A unified request function MUST encapsulate all HTTP requests with:
- Platform-specific delays (1-5 seconds)
- User-Agent pool with random rotation
- Browser-mimicking headers
- All scrapers MUST use this function exclusively
- Raw data MUST be preserved separately from cleaned data

**Rationale**: Respectful scraping prevents bans. Reproducibility requires raw data preservation. Centralized logic ensures consistency.

### VII. Testability: Dry-Run Mode

A dry-run mode toggle MUST exist. When enabled:
- Pipeline executes normally
- AI processing layers use mock data
- No actual LLM API calls made

**Rationale**: Rapid development iteration without API costs. Integration testing without external dependencies.

### VIII. MVP Mindset

Technology choices prioritize simplicity until proven inadequate:
- Database: SQLite (until scale demands otherwise)
- Task scheduling: APScheduler (until complexity demands otherwise)
- Caching: In-memory dict (until performance demands otherwise)

**Rationale**: Premature optimization wastes time. Complexity is a liability. Upgrade when bottlenecks are measured, not anticipated.

### IX. Git Discipline

Every completed and verified feature MUST be committed immediately. Commit messages MUST clearly state what was accomplished.

**Rationale**: Atomic commits enable clean rollbacks. Clear history aids debugging and onboarding. Frequent commits reduce merge conflicts.

## Technical Standards

### Error Handling Hierarchy

1. **External API failures**: Log, retry with exponential backoff (max 3 attempts), then skip
2. **Parse failures**: Log with input sample, skip item, continue pipeline
3. **Database errors**: Log, raise exception (these indicate systemic issues)

### Logging Requirements

All logs MUST include:
- Timestamp (ISO 8601)
- Log level (DEBUG/INFO/WARNING/ERROR)
- Component name
- Structured context (JSON-serializable dict)

Critical events requiring ERROR-level logs:
- API call failures after retries
- Parse failures on LLM output
- Database write failures
- Configuration load failures

### Data Retention

- Raw scraped data: 30 days minimum
- Cleaned/processed data: 90 days minimum
- AI-generated summaries: Indefinite (until user deletion)
- Logs: 7 days minimum

## Development Workflow

### Feature Development Cycle

1. **Specification**: Define inputs, outputs, edge cases in `.specify/specs/`
2. **Configuration**: Add any new parameters to config files
3. **Implementation**: Write code with defensive patterns
4. **Dry-run testing**: Verify with mock data
5. **Live testing**: Small-scale test with real APIs
6. **Commit**: Atomic commit with clear message
7. **Documentation**: Update relevant docs if behavior changes

### Code Review Checklist

Before any PR approval, verify:
- [ ] No hardcoded prompts (check `prompts/` directory)
- [ ] No hardcoded config values (check config files)
- [ ] All LLM parsing has try-except
- [ ] Input truncation applied where needed
- [ ] Logging added for pipeline stages
- [ ] Dry-run mode compatible
- [ ] Raw data preservation maintained
- [ ] Commit message describes what was done

## Governance

This constitution supersedes all other development practices. When conflicts arise between this document and other guidance, this document prevails.

### Amendment Process

1. Propose changes via documented rationale
2. Validate impact on existing codebase
3. Update dependent templates and documentation
4. Increment version according to semantic versioning:
   - **MAJOR**: Principle removal or incompatible redefinition
   - **MINOR**: New principle or material expansion
   - **PATCH**: Clarifications, wording fixes
5. Update `LAST_AMENDED_DATE` to amendment date

### Compliance Review

All pull requests MUST verify compliance with applicable principles. Violations require either:
- Code changes to comply, OR
- Constitutional amendment with documented justification

### Runtime Guidance

For AI agent development guidance, refer to `.specify/templates/agent-file-template.md` and skill-specific documentation in `.claude/skills/`.

**Version**: 1.0.0 | **Ratified**: 2026-04-08 | **Last Amended**: 2026-04-08
