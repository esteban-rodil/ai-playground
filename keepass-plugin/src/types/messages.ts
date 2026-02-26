export enum MessageType {
  GET_VAULT_STATE = 'GET_VAULT_STATE',
  GET_ACTIVE_TAB_DOMAIN = 'GET_ACTIVE_TAB_DOMAIN',
  FIND_LOGIN_FORMS = 'FIND_LOGIN_FORMS'
}

export type VaultState = 'locked' | 'unlocked';

export interface GetVaultStateRequest {
  type: MessageType.GET_VAULT_STATE;
}

export interface GetActiveTabDomainRequest {
  type: MessageType.GET_ACTIVE_TAB_DOMAIN;
}

export interface FindLoginFormsRequest {
  type: MessageType.FIND_LOGIN_FORMS;
}

export type RuntimeRequest =
  | GetVaultStateRequest
  | GetActiveTabDomainRequest
  | FindLoginFormsRequest;

export interface RuntimeResponse<T = unknown> {
  ok: boolean;
  data?: T;
  error?: string;
}
