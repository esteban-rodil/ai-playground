const MessageType = {
  GET_VAULT_STATE: 'GET_VAULT_STATE',
  GET_ACTIVE_TAB_DOMAIN: 'GET_ACTIVE_TAB_DOMAIN',
  FIND_LOGIN_FORMS: 'FIND_LOGIN_FORMS'
};

let vaultState = 'locked';

function extractDomain(url) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null;
    }
    return parsed.hostname.toLowerCase();
  } catch {
    return null;
  }
}

chrome.runtime.onInstalled.addListener(() => {
  vaultState = 'locked';
});

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request.type === MessageType.GET_VAULT_STATE) {
    sendResponse({ ok: true, data: { state: vaultState } });
    return false;
  }

  if (request.type === MessageType.GET_ACTIVE_TAB_DOMAIN) {
    (async () => {
      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const domain = tab?.url ? extractDomain(tab.url) : null;
        sendResponse({ ok: true, data: { domain } });
      } catch (error) {
        sendResponse({ ok: false, error: error?.message ?? 'Failed to query active tab' });
      }
    })();
    return true;
  }

  sendResponse({ ok: false, error: `Unhandled message type: ${request.type}` });
  return false;
});
