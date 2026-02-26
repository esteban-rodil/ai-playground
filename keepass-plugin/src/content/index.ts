import {
  MessageType,
  RuntimeRequest,
  RuntimeResponse
} from '../types/messages';

function detectLoginForms(): number {
  const forms = Array.from(document.querySelectorAll('form'));

  return forms.filter((form) => {
    const hasPasswordField = form.querySelector('input[type="password"]') !== null;
    const hasUsernameLikeField =
      form.querySelector('input[type="email"], input[type="text"], input[name*="user" i]') !== null;

    return hasPasswordField && hasUsernameLikeField;
  }).length;
}

chrome.runtime.onMessage.addListener(
  (
    request: RuntimeRequest,
    _sender,
    sendResponse: (response: RuntimeResponse) => void
  ) => {
    if (request.type === MessageType.FIND_LOGIN_FORMS) {
      sendResponse({ ok: true, data: { count: detectLoginForms() } });
      return false;
    }

    return false;
  }
);
