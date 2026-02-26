# KeePass Autofill Chrome Extension

A Chrome (Manifest V3) extension to open a local KeePass (`.kdbx`) database and fill login forms securely.

## What this plugin is for
The plugin is being developed to:
- Let you select a local KeePass database file.
- Ask for your master password to unlock the database.
- Suggest credentials matching the active website domain.
- Fill username/password fields into web login forms on explicit user action.
- Auto-lock the vault after an inactivity timeout (default target: 5 minutes).

## Current status
This repository currently contains **Milestone 1 scaffold code**:
- MV3 manifest, popup, background service worker, and content script wiring.
- Shared runtime message contracts.
- Active-tab domain extraction utility.
- Basic login-form detection wiring in the content script.

Unlocking `.kdbx` and full autofill behavior are planned in later milestones.

## Installation

### For users (future release)
When the plugin reaches release readiness:
1. Download the packaged extension ZIP.
2. Unzip it locally.
3. Open `chrome://extensions`.
4. Enable **Developer mode**.
5. Click **Load unpacked** and select the extracted extension folder.

### For developers (current repo)
1. Clone this repository.
2. Open Chrome and navigate to `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the `keepass-plugin/` folder.

> Note: for this scaffold, runtime entry files (`background.js`, `content.js`, `popup.js`) are committed so **Load unpacked** works without a build step.

## Milestone 1 structure
- `manifest.json` — extension metadata and script wiring.
- `popup.html` — popup shell.
- `src/background/index.ts` — background runtime message handling.
- `src/content/index.ts` — page-side login-form detection hook.
- `src/popup/index.ts` — popup UI initialization and status rendering.
- `src/types/messages.ts` — message contract definitions.
- `src/utils/domain.ts` — active tab domain extraction helper.
- `docs/research/chrome-keepass-plugin-plan.md` — implementation roadmap.
