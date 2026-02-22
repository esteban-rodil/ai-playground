# Claude Code Development Rules

This document specifies rules and conventions that Claude Code and other AI agents should follow when making changes to this repository.

## Code Style & Formatting

### Indentation & Whitespace
- **Java files** (`.java`): 4 spaces, LF line endings
- **Groovy files** (`.groovy`): 4 spaces, LF line endings
- **XML files** (`.xml`): 4 spaces, LF line endings
- **Python files** (`.py`): 4 spaces, PEP 8 compliant
- **JavaScript/JSON** (`.js`, `.json`): 2 spaces
- **YAML** (`.yml`, `.yaml`): 2 spaces
- **Shell scripts** (`.sh`, `.bash`): 2 spaces
- **All files**: Unix LF line endings, UTF-8 charset, final newline required

### Spock Test Conventions

All Spock specifications (`*Spec.groovy` files) MUST follow these indentation rules:

```groovy
def "test description in natural language"() {
    given:
        // Setup code indented 4 spaces from 'given:' label
        def setup = value

    when:
        // Action code indented 4 spaces from 'when:' label
        def result = action()

    then:
        // Assertion code indented 4 spaces from 'then:' label
        result == expected

    where:
        // Parameterized test data indented 4 spaces
        input || expected
        1     || 2
        3     || 4
}
```

**Key rules:**
1. Block labels (`given:`, `when:`, `then:`, `expect:`, `where:`, etc.) are at the method indentation level
2. Code within blocks is indented 4 spaces (one additional level) from the label
3. Multi-block tests must maintain consistent indentation across all blocks
4. Single-block tests (e.g., `expect:` only) also follow the same pattern

### Test File Organization

```groovy
package com.netflow.parser

import necessary.dependencies.*
import spock.lang.Specification
import org.springframework.boot.test.context.SpringBootTest

@SpringBootTest
class MyFeatureSpec extends Specification {

    @Autowired
    SomeService service

    def "descriptive test name"() {
        // test body with proper indentation
    }
}
```

## Git Commit Conventions

### Commit Message Format
```
type(scope): brief description

Optional longer explanation if needed.

https://claude.ai/code/session_<SESSION_ID>
```

**Valid types:**
- `feat` — New feature
- `fix` — Bug fix
- `test` — Test additions or fixes
- `docs` — Documentation changes
- `style` — Code style, formatting, or EditorConfig updates
- `refactor` — Code refactoring without changing behavior
- `chore` — Build, dependency, or tooling updates

**Scope examples:** `M1.S2`, `netflow-java`, `build-helper`

### Examples
```
feat(M1.S2): add Spring Boot application entry point
test(M1.S2): add Spock spec validating Spring context loads
docs(M1.S1): mark story as done, record implementation decisions
style: add EditorConfig rules and fix Spock test indentation
```

## Branch Naming

- Development branches MUST be named: `claude/implement-next-task-<SESSION_ID>` or `claude/<task-name>-<SESSION_ID>`
- Branches must start with `claude/` and end with the session ID (matching the session URL)
- Always push with `-u` flag: `git push -u origin <branch-name>`

## Maven Build

### Build Helper
Use the provided Maven proxy build helper for all builds in network-restricted environments:

```bash
./scripts/build-helper/build.sh clean compile
./scripts/build-helper/build.sh clean test
./scripts/build-helper/build.sh clean package
```

**Never use** `mvn` directly in restricted network environments — use the build helper script instead.

### Build Verification
After making code changes:
1. Run `./scripts/build-helper/build.sh clean compile` — verify compilation
2. Run `./scripts/build-helper/build.sh clean test` — verify all tests pass
3. Only commit if both succeed

## Project Structure

### netflow-java
- Source code: `src/main/java/com/netflow/`
- Tests: `src/test/groovy/com/netflow/`
- Resources: `src/main/resources/`, `src/test/resources/`
- Build configuration: `pom.xml`
- Task tracking: `docs/tasks/netflow-parser-stories.md`
- Implementation plans: `docs/plans/netflow-parser-implementation-plan.md`

### Task Status Updates
When completing a story (e.g., M1.S2):
1. Update `netflow-java/docs/tasks/netflow-parser-stories.md`
2. Change status from `[ ]` (pending) to `[x]` (done)
3. Add `> **Status:** ✅ Done` line after story title
4. Include story ID and status in commit message

## EditorConfig Compliance

Repository uses `.editorconfig` files at:
- `/home/user/ai-playground/.editorconfig` (root rules)
- `/home/user/ai-playground/netflow-java/.editorconfig` (Spock conventions)

These settings are automatically enforced by compatible editors/IDEs (VS Code, IntelliJ, etc.).

## Critical Rules for AI Agents

1. **Always verify builds pass** before committing
2. **Follow Spock indentation strictly** — test readability depends on it
3. **Commit after each meaningful change** — don't batch unrelated work
4. **Include session URL in commit message** — for traceability
5. **Never force-push** without explicit user authorization
6. **Update task status** when completing stories
7. **Use build helper script** — never bypass proxy authentication issues with `--no-verify` or similar

## Story Completion Checklist

Before marking a story complete:
- [ ] All acceptance criteria met
- [ ] Code compiles: `./scripts/build-helper/build.sh clean compile`
- [ ] All tests pass: `./scripts/build-helper/build.sh clean test`
- [ ] Code follows style guidelines (EditorConfig)
- [ ] Spock tests follow indentation rules
- [ ] Story status updated in `netflow-parser-stories.md`
- [ ] Changes committed with descriptive message
- [ ] Changes pushed to designated branch

---

**Last updated:** 2026-02-22
**Applies to:** All AI agent development on this repository
