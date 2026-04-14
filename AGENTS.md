# AGENTS.md

## Project Context
- Drinout backend application.
- Stack: Python backend with the current repository structure as the source of truth.
- Prioritize small, clear changes aligned with the existing architecture.
- Before modifying shared logic, evaluate impact across `app`, `models`, `schemas`, `utils`, and any request/DB flow that depends on them.
- Development database credentials are stored in the local `.env` file for this repository. Check `.env` before doing local DB connectivity work.

## Working Preferences
- Do not spend time on unit tests unless explicitly requested.
- For maintenance or adjustments, prioritize implementation and functional validation over test coverage.
- Avoid unnecessary changes outside the requested scope.
- Do not refactor working code purely for style.

## Backend Guidelines
- Maintain consistency between routes, schemas, models, and persistence logic.
- When adding or changing an endpoint, validate whether request validation, response schema, database access, and shared utilities also need updates.
- Avoid duplicating business rules if a single source of truth can be used.
- Any operation that changes critical state must handle failure paths explicitly and return clear errors.
- Be especially careful with shared utilities, database session usage, and data shape changes.
- Before modifying shared backend flows, evaluate impact on:
  - request validation
  - serialization/deserialization
  - database writes and reads
  - backward compatibility for existing consumers

## Editing Guidelines
- Apply the smallest safe change first.
- Do not rewrite functional code unless necessary to meet the requirement.
- Avoid changes outside the requested scope.
- Prefer reusing existing services, helpers, and patterns over creating new ones.
- If ambiguity is minor, infer from existing project patterns.
- Ask only when ambiguity blocks a safe or correct implementation.
- When modifying shared logic, consider side effects across related modules.

## Verification
- When possible, validate changes using local functional checks, targeted tests, or startup/build checks.
- Do not invest time in test suites unless explicitly requested.
- If verification was not performed, state it clearly.

## Response Style
- Be concise by default.
- Remove filler, pleasantries, and unnecessary narrative.
- Prefer short, direct sentences.
- Preserve technical accuracy at all times.
- Keep exact code, paths, identifiers, commands, diffs, and commit messages intact.
- Do not omit relevant warnings, constraints, or risks.
- For code changes, always include:
  1. what changed
  2. why
  3. how to verify

## Compression Modes
- Required skill: `caveman`.
- Install command: `npx skills add JuliusBrussee/caveman`.
- If `caveman` is available, use it as the repository communication rule.
- If `caveman` is not installed, not available in the session, or cannot be applied, fall back to the short, concise response style already defined in this `AGENTS.md`.
- Default: `caveman full`.
- If the user says `caveman`, switch to highly compressed output.
- If the user says `normal mode`, return to standard concise output.
- Compression affects wording only, never technical accuracy, safety, or completeness.

## Caveman Reference
- Reference: https://github.com/JuliusBrussee/caveman
- Install with: `npx skills add JuliusBrussee/caveman`
- Treat `caveman` as a communication rule for collaborators, not as a project dependency.

## Repository Rule
- `AGENTS.md` must remain versioned in this repository so other developers and agents can follow the same collaboration rules.
