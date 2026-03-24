---
name: commit-push-done
description: Stage, commit with conventional message, push, merge to main, push main, and delete the feature branch
disable-model-invocation: true
allowed-tools: Bash(git *)
---

# Commit, Push, Merge & Cleanup

Execute this workflow in order. Do not skip steps.

## Step 1: Check Context

```bash
git branch --show-current
git status --porcelain
```

Abort if on `main` or `master` — this command is for feature branches only.

## Step 2: Stage Changes

```bash
git add -A
```

## Step 3: Generate & Commit

Analyze `git diff --staged` and produce a conventional commit message:
- Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Scope: optional, e.g. dashboard, reports
- Description: imperative, present tense, &lt;72 chars

Example: `fix: remove org-specific user refs from dashboard for deployability`

```bash
git commit -m "<type>[scope]: <description>"
```

Never use the `--trailer` switch with `git commit` in this workflow.

If commit fails (e.g. hooks), fix issues and create a new commit. Never use `--no-verify` unless the user explicitly asks.

## Step 4: Run Unit Tests (Required)

Run the full unit test suite for this repository using this exact command:

```bash
python3 -m pytest ".cursor/skills/cosmic-measurer"
```

If tests fail, stop this workflow, fix the failures on the feature branch, and re-run the full command until it passes.

## Step 5: Push

```bash
git push -u origin $(git branch --show-current)
```

## Step 6: Switch to Main & Pull

```bash
git checkout main
git pull origin main
```

Use `master` instead of `main` if that is the default branch.

## Step 7: Merge Feature Branch into Main

```bash
git merge <feature-branch-name> --no-ff -m "Merge branch '<feature-branch-name>'"
```

Use the branch name from Step 1. Resolve any merge conflicts if they occur.

## Step 8: Push Main

```bash
git push origin main
```

## Step 9: Delete the Feature Branch

```bash
git branch -d <feature-branch-name>
git push origin --delete <feature-branch-name>
```

Use the branch name from Step 1. If `-d` fails (unmerged changes), stop and report — do not use `-D` unless the user explicitly asks.

## Success

- Changes committed with conventional message
- Branch pushed to remote
- Merged into main
- Main pushed to remote
- Local and remote feature branch deleted
