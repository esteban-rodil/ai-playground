import {
  MessageType,
  RuntimeRequest,
  RuntimeResponse,
  VaultState
} from '../types/messages';
import { extractDomain } from '../utils/domain';

let vaultState: VaultState = 'locked';

chrome.runtime.onInstalled.addListener(() => {
  vaultState = 'locked';
});

chrome.runtime.onMessage.addListener(
  (
    request: RuntimeRequest,
    _sender,
    sendResponse: (response: RuntimeResponse) => void
  ) => {
    if (request.type === MessageType.GET_VAULT_STATE) {
      sendResponse({ ok: true, data: { state: vaultState } });
      return false;
    }

    if (request.type === MessageType.GET_ACTIVE_TAB_DOMAIN) {
      void (async () => {
        try {
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          const domain = tab?.url ? extractDomain(tab.url) : null;
          sendResponse({ ok: true, data: { domain } });
        } catch (error) {
          sendResponse({
            ok: false,
            error: error instanceof Error ? error.message : 'Failed to query active tab'
          });
        }
      })();
      return true;
    }

    sendResponse({ ok: false, error: `Unhandled message type: ${request.type}` });
    return false;
  }
);
