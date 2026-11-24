import { api, getSessionId } from "./client";

export function sendChatMessage(message, history = []) {
  return api.post("/api/assistant/chat", {
    session_id: getSessionId(),
    message,
    history,
  });
}
