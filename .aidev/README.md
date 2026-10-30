# Automated contributions

This directory configures the automated development platform that contributes to this
repository. This note says which branches it uses here and how its work reaches the
project's main line.

## Branches

- `aidev/integration` — the integration branch. Automated work lands here and nowhere else.
- `develop` — the project's main line; reached from `aidev/integration` only by merge request
  (`aidev handoff`). Merge integration MRs **keeping the source branch**
  (`aidev/integration` is protected, so GitLab never deletes it). `master` is reached from
  `develop` by this project's own process; the platform never touches it.
- `ai/*` — one branch per task, created and deleted by the platform. Do not commit to them.
- `session/*` — a session's accumulated work, landed on the integration branch as a batch.

## How work reaches the main line

Task and session branches never reach `aidev/integration` through merge requests; the platform
lands them after its own verification. `aidev/integration` reaches `develop` by this project's
usual process, merge requests included — the platform never merges into any other branch.

Whether this project's CI pipelines skip `ai/*` and `session/*` branches is decided by the
project's CI rules: today `.gitlab-ci.yml` has only the two deploy jobs, `deploy_staging`
(`only: develop`, to signup-staging.hive.io) and `deploy_master` (`only: master`, to
signup.hive.io), so no other branch and no merge request gets a pipeline. **Every push to
`develop` deploys staging**, merging an integration MR included.

The deploy runs `aws s3 sync .` excluding only `.git/*`, `.gitlab-ci.yml` and `README.md`,
so it also publishes `.aidev/` (and `CLAUDE.md`) to the bucket. They hold no secrets; add
an `--exclude ".aidev/*"` to the deploy jobs if that is unwanted.

**Auto DevOps is on for this project** (project-level setting, Settings > CI/CD > Auto
DevOps). It only acts on a pushed branch that has no `.gitlab-ci.yml`; every branch here
carries one, so it should not start pipelines, but turn it off if a branch ever shows
Auto DevOps jobs (`secret_detection`, `build`, ...).

## Suites run before work lands

The repository is one static page with no build, no package manager and no tests, so the
slots run static checks of it. Declared in `.aidev/project.yaml` under `verification`, all
through `.aidev/run-checks.py` (standard-library Python), which writes
`test-results/<slot>/junit.xml`:

- `quick`, `full`, `canary`, `coverage`, `system` — `html assets svg`
- `baseline` — `assets svg`
- `static` — `html svg`

`html`: `index.html` parses and every non-void element it opens is closed in order.
`assets`: every repository-relative `src=`, `href=` or CSS `url()` in `index.html` names a
file that exists. `svg`: every `images/*.svg` is well-formed XML. The set takes under a
second. There is no coverage tool, so `coverage` repeats the checks without measuring;
`system` has no services to run against and repeats them too.

### Excluded (already failing on `develop`)

- In `html`, the footer's two outer `<div>`s (`class="footer layout__footer"` and
  `class="footer__inner"`) are never closed; `</body>` closes them. They are excluded by tag
  and class (`KNOWN_UNCLOSED` in `.aidev/run-checks.py`); remove the entry once the page
  closes them.

### Not run (network)

- The deploy jobs (`aws s3 sync`, CloudFront invalidation).
- Any check of the external links and CDN assets the page loads (Bootstrap, jQuery, Popper,
  Google Fonts, Google Tag Manager).

`test-results/` is not in `.gitignore`; do not commit it.

## Test runtime

The checks need only Python's standard library, so the profile pins Docker Hub's
`python:3-alpine` by digest and builds no image of its own. Move the digest forward by
editing `environment.image`.
