---
name: release
description: Git, versioning, and release/publish workflow for the cftc-cot (cftc-cot-soda) package. Use for ANY git-related work in this repo — branching, commits, version bumps, tagging, cutting a release, or publishing to PyPI. Enforces the Git-Flow (develop→master) + manual-twine process this project uses.
---

# cftc-cot release & git workflow

This repo (`cftc-cot`, published to PyPI as **`cftc-cot-soda`**) uses **Git-Flow**
and **SemVer**. Full reference: [RELEASING.md](../../../RELEASING.md). Follow the
rules below for any git-related task here.

## Branching (Git-Flow)
- `develop` = integration/working branch. Do all work here (or feature branches off it).
- `master` = production; only updated via a `--no-ff` merge from `develop` at release time.
- Never commit feature work directly to `master`.
- Tags are `vX.Y.Z` (annotated), created on `master`.

## Commit conventions
- Conventional-commit style: `feat(scope): …`, `fix(scope): …`, `docs: …`, `chore: …`.
- A version bump rides on its commit: `feat(...): <summary>; bump to X.Y.Z`.
- **No `Co-Authored-By` trailer** (disabled globally for this user). Don't add it.

## Cutting a release
Run the steps in [RELEASING.md](../../../RELEASING.md). The essentials:

1. **Pre-flight on `develop`**: `pytest -q`, then `python -m build` + `twine check dist/*`. Don't release on red.
2. **Bump in two files, kept in sync**: `pyproject.toml` `version` and `src/cftc_cot/__init__.py` `__version__`.
3. **Docs that move with the release**:
   - `CHANGELOG.md` — new `## [X.Y.Z] - YYYY-MM-DD` at the top.
   - The **wiki is a separate repo** (`../cftc-cot-wiki`, remote `cftc-cot.wiki`): mirror the changelog entry, bump `@vX.Y.Z` install URLs in `Installation.md`/`README.md`, and update any changed API page. Commit & push it separately.
4. **Commit on `develop`** → **merge `--no-ff` into `master`** (`"Merge develop into master for vX.Y.Z release"`) → **tag `vX.Y.Z`** → **push `develop master vX.Y.Z`**.
5. **GitHub release**: `gh release create vX.Y.Z …` then `gh release upload vX.Y.Z dist/*` to attach the local build.
6. **Publish** (see gotcha below).

## ⚠️ Publishing gotcha — CI is billing-locked
The `Publish to PyPI` GitHub Action (`.github/workflows/publish.yml`, Trusted
Publishing on `release: published`) currently **fails on every release**:
*"account locked due to a billing issue"* (v0.2.1, v0.3.0, v0.4.0 all failed).

Until GitHub Actions billing is restored, **publish manually**:
```bash
venv/bin/python -m twine upload dist/cftc_cot_soda-X.Y.Z*   # uses ~/.pypirc
```
When CI is restored, the release event publishes automatically and you can
`gh run rerun <id>` a failed run instead. Always verify afterward:
`https://pypi.org/pypi/cftc-cot-soda/X.Y.Z/json` should return `200`.

## Repo facts
- GitHub: `victorKariuki/cftc-cot` (HTTPS, `gh` authed as `victorKariuki`).
- Wiki: `victorKariuki/cftc-cot.wiki` → checked out at `../cftc-cot-wiki`.
- `dist/`, `build/`, `*.egg-info/` are gitignored — safe to build in-tree.
