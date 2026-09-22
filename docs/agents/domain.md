# Domain Docs

How engineering skills should consume this repository's domain documentation.

## Before exploring, read these

- `CONTEXT.md` at the repository root.
- `docs/adr/` entries relevant to the area being changed.

If either location does not exist, proceed silently. Domain documentation and
ADRs are created only when actual terminology or architectural decisions require
them.

## File structure

This is a single-context repository:

```text
/
├── CONTEXT.md
├── docs/adr/
└── source files
```

## Use the glossary's vocabulary

When an issue, test, proposal, or implementation names a domain concept, use the
term defined in `CONTEXT.md`. Avoid synonyms that the glossary explicitly
rejects.

If a required concept is missing, reconsider whether new terminology is
necessary or record the gap for domain modeling.

## Flag ADR conflicts

Explicitly identify proposals that contradict an existing ADR instead of
silently overriding the decision.
