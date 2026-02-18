const MessageType = {
  GET_VAULT_STATE: 'GET_VAULT_STATE',
  GET_ACTIVE_TAB_DOMAIN: 'GET_ACTIVE_TAB_DOMAIN'
};

const app = document.getElementById('app');

if (!app) {
  throw new Error('Popup root element not found');
}

async function getVaultState() {
  const response = await chrome.runtime.sendMessage({ type: MessageType.GET_VAULT_STATE });

  if (!response?.ok || !response?.data) {
    throw new Error(response?.error ?? 'Unknown vault state error');
  }

  return response.data.state;
}

async function getActiveDomain() {
  const response = await chrome.runtime.sendMessage({ type: MessageType.GET_ACTIVE_TAB_DOMAIN });

  if (!response?.ok || !response?.data) {
    throw new Error(response?.error ?? 'Unknown active tab domain error');
  }

  return response.data.domain;
}

async function render() {
  const [state, domain] = await Promise.all([getVaultState(), getActiveDomain()]);

  app.innerHTML = `
    <main>
      <h1>KeePass Autofill</h1>
      <p><strong>Vault state:</strong> ${state}</p>
      <p><strong>Active domain:</strong> ${domain ?? 'Unavailable'}</p>
      <p>Milestone 1 scaffold is active.</p>
    </main>
  `;
}

render().catch((error) => {
  app.innerHTML = `<p>Failed to initialize popup: ${error?.message ?? 'Unknown error'}</p>`;
});
