# Task Completion Checklist

Use this checklist when completing any story or feature task. All items must be verified before committing.

## Pre-Coding Phase

- [ ] Story requirements clearly understood
- [ ] Acceptance criteria listed and reviewed
- [ ] Dependencies satisfied (previous stories complete)
- [ ] No existing conflicting work

## Development Phase

### Code Implementation
- [ ] Feature/fix implemented according to spec
- [ ] Code follows project style guidelines (EditorConfig)
- [ ] No debug code, commented-out code, or TODOs left behind
- [ ] Variable names are clear and descriptive

### Spock Tests (if applicable)
- [ ] Test file created with `*Spec.groovy` naming
- [ ] Test class extends `Specification`
- [ ] Block labels (given:, when:, then:, expect:) at base indentation
- [ ] Code within blocks indented 4 additional spaces
- [ ] All acceptance criteria have corresponding tests
- [ ] Edge cases covered

### Java/Groovy Code Quality
- [ ] No unused imports
- [ ] Proper exception handling
- [ ] Constants used instead of magic numbers
- [ ] Meaningful class and method names

## Build & Test Phase

### Compilation
- [ ] `./scripts/build-helper/build.sh clean compile` succeeds
- [ ] No compiler warnings
- [ ] No errors in build output

### Test Execution
- [ ] `./scripts/build-helper/build.sh clean test` succeeds
- [ ] All tests pass (0 failures, 0 errors)
- [ ] No skipped tests
- [ ] Test output is clean (only informational logs)

### Coverage (if applicable)
- [ ] New code has test coverage
- [ ] No regression in existing tests

## Documentation Phase

### Code Documentation
- [ ] Public classes/methods have JavaDoc (for Java)
- [ ] Complex logic has explanatory comments
- [ ] README updated if behavior changed

### Task Tracking
- [ ] Story file (`netflow-parser-stories.md`) updated:
  - [ ] Status changed from `[ ]` (pending) to `[x]` (done)
  - [ ] `> **Status:** ✅ Done` added after story title
  - [ ] All acceptance criteria marked `[x]`

## Git Phase

### Staging & Committing
- [ ] Only relevant files staged (use `git status` to verify)
- [ ] Commit message format:
  - [ ] Type specified: `feat`, `fix`, `test`, `docs`, `style`, `refactor`, `chore`
  - [ ] Scope in parentheses: `(M1.S2)` or `(build-helper)`
  - [ ] Brief description: under 70 characters
  - [ ] Session URL included: `https://claude.ai/code/session_...`
- [ ] No unintended files committed (check `.gitignore`)

### Pushing
- [ ] On correct branch: `claude/implement-next-task-<SESSION_ID>`
- [ ] Push command: `git push -u origin <branch-name>`
- [ ] No force-push used
- [ ] Remote shows new commits

## Final Verification

- [ ] All acceptance criteria verified as complete
- [ ] Build passes: `./scripts/build-helper/build.sh clean compile`
- [ ] Tests pass: `./scripts/build-helper/build.sh clean test`
- [ ] Code follows style guidelines
- [ ] Commit message is clear and includes session URL
- [ ] Changes are pushed to designated branch

## Sign-Off

- [ ] Checklist completed
- [ ] Ready for user review

---

## Quick Reference: Common Commands

### Build & Test
```bash
# Compile only
./scripts/build-helper/build.sh clean compile

# Run tests
./scripts/build-helper/build.sh clean test

# Full build with package
./scripts/build-helper/build.sh clean package
```

### Git Operations
```bash
# Check status
git status

# Stage changes
git add <files>

# Commit
git commit -m "type(scope): description
https://claude.ai/code/session_ID"

# Push
git push -u origin claude/implement-next-task-<SESSION_ID>

# View log
git log --oneline -10
```

### Verify Changes
```bash
# See what's changed
git diff HEAD

# See staged changes
git diff --cached

# See differences from main
git diff main..HEAD
```

---

**Last updated:** 2026-02-22
**Applies to:** All story implementations and feature work
