# Releasing cftc-cot

How a new version of **`cftc-cot-soda`** is cut, released, and published to PyPI.
This project follows **Git-Flow** (`develop` → `master`) and **SemVer**, with tags
`vX.Y.Z`.

> ⚠️ **CI publish is currently broken.** The GitHub Actions *Publish to PyPI*
> workflow fails on every release with *"account locked due to a billing issue"*
> (see runs for v0.2.1, v0.3.0, v0.4.0). Until the Actions billing is restored,
> **publish manually with twine** (step 7). The release/tag/flow is otherwise
> unchanged.

## Pipeline overview

```
develop  ──commit──▶ merge --no-ff ──▶ master ──tag vX.Y.Z──▶ GitHub Release
                                                                    │
                                          (intended) Trusted Publishing CI ─┐
                                                                    │       │ ✗ billing-locked
                                                                    ▼       ▼
                                                              PyPI  ◀── manual twine (current)
```

- **Trigger (intended):** `.github/workflows/publish.yml` runs on
  `release: published` and uploads via PyPI **Trusted Publishing** (OIDC, no token).
- **Fallback (current):** `twine upload` from local using `~/.pypirc`.

## Versioning

Bump **both**, kept in sync:
- `pyproject.toml` → `version = "X.Y.Z"`
- `src/cftc_cot/__init__.py` → `__version__ = "X.Y.Z"`

SemVer: new backward-compatible features → **minor**; fixes only → **patch**.

## Documentation that must move with a release

- `CHANGELOG.md` (this repo) — new `## [X.Y.Z] - YYYY-MM-DD` section at the top.
- Wiki repo (`cftc-cot.wiki`, separate git repo, default branch `master`):
  - `Changelog.md` — mirror the package changelog entry (newest first).
  - `Installation.md` + `README.md` — bump the GitHub `@vX.Y.Z` / release-wheel URLs.
  - Any page documenting changed/added API (e.g. `COTClient.md`, `COTQuery-Builder.md`).

## Step-by-step

```bash
# 0. Pre-flight (on develop)
PYTHONPATH=src venv/bin/python -m pytest -q
rm -rf dist build src/*.egg-info
venv/bin/python -m build
venv/bin/python -m twine check dist/*

# 1. Bump version in pyproject.toml + src/cftc_cot/__init__.py
# 2. Update CHANGELOG.md (and the wiki docs, pushed separately)

# 3. Commit on develop  (no Co-Authored-By trailer — disabled globally)
git add -A
git commit -m "feat(...): <summary>; bump to X.Y.Z"

# 4. Merge develop -> master
git checkout master
git merge --no-ff develop -m "Merge develop into master for vX.Y.Z release"

# 5. Tag + push
git tag -a vX.Y.Z -m "vX.Y.Z — <summary>"
git push origin develop master vX.Y.Z

# 6. GitHub Release (+ attach the local build as assets)
gh release create vX.Y.Z --repo victorKariuki/cftc-cot \
  --title "vX.Y.Z — <summary>" --notes "<release notes>"
gh release upload vX.Y.Z dist/cftc_cot_soda-X.Y.Z-py3-none-any.whl \
  dist/cftc_cot_soda-X.Y.Z.tar.gz --repo victorKariuki/cftc-cot

# 7. Publish to PyPI  (manual fallback while CI is billing-locked)
venv/bin/python -m twine upload dist/cftc_cot_soda-X.Y.Z*
#    When CI is restored instead: the release event publishes automatically;
#    re-run a failed run with `gh run rerun <id>`.

# 8. Wiki repo (separate checkout)
git -C ../cftc-cot-wiki add -A
git -C ../cftc-cot-wiki commit -m "docs: document vX.Y.Z"
git -C ../cftc-cot-wiki push origin HEAD
```

## Verify

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/cftc-cot-soda/X.Y.Z/json   # 200
curl -s https://pypi.org/pypi/cftc-cot-soda/json | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])"
```

(The version-specific endpoint updates first; the top-level `info.version` can lag a minute on cache.)
