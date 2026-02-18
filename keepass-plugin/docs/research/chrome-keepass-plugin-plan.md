# Chrome KeePass Autofill Plugin – Development Plan

## 1) Goal and Scope
Build a Chrome extension (Manifest V3) that:
- Lets users choose a KeePass database file (`.kdbx`) from local disk.
- Prompts users for the master password when opening the database.
- Parses the KeePass file in-memory and allows selecting credentials for a site.
- Fills login forms on webpages securely (username, password, optional TOTP later).
- Locks the opened database automatically after a configurable inactivity timeout (default: 5 minutes).

Out of scope for first milestone:
- Writing changes back to the `.kdbx` file.
- Cloud sync and multi-device storage.
- Full KeePass feature parity (attachments, custom plugins, advanced triggers).

## 2) Architecture Proposal
### Extension components
1. **Popup UI**
   - Database file picker.
   - Master password input.
   - “Unlock” / “Lock” actions.
   - Quick credential search for current tab domain.

2. **Background service worker**
   - Central state coordinator (locked/unlocked).
   - Receives parsed entries from unlock flow.
   - Handles secure message routing between popup and content scripts.

3. **Content script**
   - Detects login forms in the active page.
   - Receives selected credential from background/popup.
   - Performs controlled field filling and optional submit.

4. **Offscreen document / worker (recommended)**
   - Run KeePass parsing and crypto-heavy operations away from popup lifecycle.
   - Avoid popup closing mid-decryption.

### Data handling model
- Keep decrypted database and derived keys only in volatile memory.
- Persist only non-sensitive UI preferences in `chrome.storage.local`.
- Never store master password or plaintext credentials in extension storage.

## 3) Technology Choices (TypeScript)
- **Language**: TypeScript
- **Build tooling**: Vite + CRX-compatible plugin OR esbuild-based pipeline.
- **UI**: Minimal React or vanilla TS + lit-html (choose one in implementation spike).
- **KeePass parser/crypto**: Evaluate:
  - `kdbxweb` (primary candidate)
  - Alternatives only if browser compatibility issues appear.

Deliverable from this phase:
- Decision record in `keepass-plugin/docs/research/tech-decisions.md` comparing bundle size, MV3 compatibility, and maintenance health.

## 4) Feature Breakdown by Milestone
### Milestone 1 — Extension skeleton
- Create MV3 manifest and wire popup/background/content scripts.
- Add message bus contracts (`types/messages.ts`).
- Add domain extraction utility for active tab.

### Milestone 2 — Database open/unlock flow
- Implement file picker in popup.
- Read `.kdbx` as `ArrayBuffer`.
- Prompt for master password and attempt unlock.
- Surface clear errors (bad password, corrupt DB, unsupported format).

### Milestone 3 — Credential discovery
- Parse entries and index by URL/domain.
- For current tab domain, show matching entries first.
- Add manual search across title/username/url.

### Milestone 4 — Autofill engine
- Detect candidate username/password fields robustly.
- Fill values via content script with user action.
- Add safeguards for iframes and multiple forms.

### Milestone 5 — Security hardening
- Add explicit lock button and configurable inactivity timeout (default: 5 minutes).
- Zero sensitive memory references where feasible.
- Threat-model review and permissions minimization.

### Later stage — Future authentication enhancements
- Add optional biometric-assisted unlock flow (e.g., WebAuthn/passkey-backed gate) as a convenience layer.
- Keep master password as the source of truth for vault decryption.
- Define fallback path when biometrics are unavailable or fail.

### Milestone 6 — QA and packaging
- Unit tests for parser adapters, matching logic, and message contracts.
- Manual browser test matrix for major login form patterns.
- Package signed build instructions and release checklist.

## 5) Security & Privacy Requirements
- Principle of least privilege permissions:
  - `activeTab`, `scripting`, `storage`, and narrowly scoped host permissions.
- No outbound network transfer of credentials.
- CSP compatible with MV3; no dynamic code eval.
- Lock state defaults to locked on browser restart/service worker restart.
- Auto-lock on inactivity must be configurable and default to 5 minutes.
- Clear user-facing warning that secrets remain local and in-memory only.

## 6) UX Requirements
- First-run flow:
  1. “Select KeePass file”
  2. “Enter master password”
  3. “Unlock successful” + matching credentials list
- Error messages must be actionable and non-technical where possible.
- Autofill should require explicit user choice (no silent auto-fill by default).
- Include settings screen with inactivity timeout control (default prefilled to 5 minutes).

## 7) Development Tasks (Initial Backlog)
1. Bootstrap TypeScript MV3 project under `keepass-plugin/`.
2. Implement shared types (`CredentialEntry`, `VaultState`, message enums).
3. Build popup unlock form and state transitions.
4. Integrate KeePass parser adapter with test fixtures.
5. Implement domain matcher and ranking.
6. Implement content script field discovery + fill action.
7. Add configurable lock timeout (default 5 minutes) and manual lock.
8. Add logging strategy with sensitive-data redaction.
9. Add CI checks (lint, typecheck, test, build).
10. Design biometric unlock extension point for later milestone (without weakening master-password-based security).

## 8) Risks & Mitigations
- **Risk**: MV3 service worker lifecycle drops state.
  - **Mitigation**: Keep encrypted source and prompt re-unlock when needed; optionally cache non-sensitive metadata.

- **Risk**: KDBX crypto performance for large vaults.
  - **Mitigation**: Parse in worker/offscreen context and provide progress UI.

- **Risk**: Form heuristics fail on custom login UIs.
  - **Mitigation**: Provide manual field selection fallback in content script UI.

## 9) Definition of Done (MVP)
- User can select a `.kdbx` file and unlock with password.
- Extension shows credentials relevant to current domain.
- User can click an entry to fill username/password in current page.
- Extension can lock/unlock without persisting secrets, including automatic lock after 5 minutes by default.
- Basic automated tests pass and manual QA checklist is completed.

## 10) Next Immediate Steps
1. Scaffold project files in `keepass-plugin/` using TypeScript MV3 template.
2. Create a tiny unlock proof-of-concept using chosen KeePass library.
3. Validate autofill on 3 representative sites (simple form, SPA form, iframe form).
4. Freeze MVP API contracts before full implementation.
