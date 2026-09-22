# Incident: planted token detected by gitleaks (Lab 6 drill)

**Status:** closed (drill — no real credential was ever involved)
**Detected:** 2026-09-22, by a local `gitleaks detect` run before any push
**Severity if real:** high — a GHCR token can push images the deployment pipeline trusts

## What happened

A fake GHCR token string was committed to `throwaway_leak.txt` and caught by a
local gitleaks scan before it reached a shared branch.

```
RuleID:      github-pat
Entropy:     4.546439
File:        throwaway_leak.txt
Line:        1
Fingerprint: throwaway_leak.txt:github-pat:1
```

The value was generated randomly for this drill and was never issued by GitHub.
A real credential would be handled by exactly the steps below — the order is the
whole lesson.

## Response (in order — this order is not negotiable)

1. **ROTATE FIRST.** Treat the token as burned the moment it was committed, even
   locally, even before any push. Revoke it at the source
   (GitHub → Settings → Developer settings → Tokens) and issue a replacement.
   Rotate related tokens too — assume lateral discovery, not just this one
   credential.

2. **CLEAN HISTORY SECOND**, only after rotation. Remove the file, rewrite
   history if it already reached a shared branch (`git filter-repo` or BFG), and
   force-push with the team's awareness. Deleting the commit does **NOT** un-leak
   a live credential — it only cleans up evidence after the credential is
   already safe.

3. **Add gitleaks as a required CI check** so this class of leak cannot merge
   silently again. Added in this lab as the `secrets` job in
   `.github/workflows/ci.yml`, and wired into `publish`'s `needs:` so an image
   is never published from a commit that carries a secret.

### Why rotate-before-clean, stated plainly

The instinct most people reach for under pressure is "I removed the commit,
we're fine." It is not fine. Once committed, the secret exists in every clone,
every fork, the reflog, and any backup taken before the cleanup. Deleting a
commit does not un-leak what it contained. Rotation always comes first; history
cleanup is what you do once the leaked credential can no longer be used for
anything.

## Underlying fix (the practice, not the symptom)

Registry credentials belong in environment variables served by the platform's
secret store — never in a committed file:

- CI authenticates to GHCR with the short-lived `GITHUB_TOKEN`, scoped by
  `permissions: packages: write` on the `publish` job alone. No long-lived PAT
  is stored as a repository secret.
- If the service itself ever needs the value, it reads it through
  `Settings.registry_token`, typed `SecretStr | None` — masked in every repr,
  print, and log line, and readable only through one explicit
  `.get_secret_value()` call site.
- `src/fraud_service/logging_setup.py` masks any field named `token`, `secret`,
  `password`, `national_id`, or `card_number` as `***MASKED***` before the JSON
  renderer runs. That is a defensive net, not permission to log secrets.

## Verification

```
$ gitleaks detect --source . --no-git -v
INF no leaks found
```

`throwaway_leak.txt` was removed with `git rm` and the drill file is gone from
the working tree.
