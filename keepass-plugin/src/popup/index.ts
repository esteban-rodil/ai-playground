import { MessageType, RuntimeResponse, VaultState } from '../types/messages';

const app = document.getElementById('app');

if (!app) {
  throw new Error('Popup root element not found');
}

async function getVaultState(): Promise<VaultState> {
  const response = (await chrome.runtime.sendMessage({
    type: MessageType.GET_VAULT_STATE
  })) as RuntimeResponse<{ state: VaultState }>;

  if (!response.ok || !response.data) {
    throw new Error(response.error ?? 'Unknown vault state error');
  }

  return response.data.state;
}

async function getActiveDomain(): Promise<string | null> {
  const response = (await chrome.runtime.sendMessage({
    type: MessageType.GET_ACTIVE_TAB_DOMAIN
  })) as RuntimeResponse<{ domain: string | null }>;

  if (!response.ok || !response.data) {
    throw new Error(response.error ?? 'Unknown active tab domain error');
  }

  return response.data.domain;
}

async function render(): Promise<void> {
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

void render().catch((error) => {
  app.innerHTML = `<p>Failed to initialize popup: ${error instanceof Error ? error.message : 'Unknown error'}</p>`;
});
