## Summary

What does this change add or clarify?

## Evidence

What example, issue, fixture, or feedback supports the change?

## Validation

Which checks did you run?

- [ ] `python -m ruff check .`
- [ ] `acp examples verify`
- [ ] `python -m pytest -q`
- [ ] `python -m build`
- [ ] `python scripts/check_distribution.py`

## Scope Check

- [ ] This keeps ACP focused on reviewable change proposals.
- [ ] This does not add a new agent runtime, hosted service, or auto-deploy loop.
- [ ] Public fixtures are sanitized and contain no sensitive traces or prompts.
