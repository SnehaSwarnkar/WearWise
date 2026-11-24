import { api, getSessionId } from "./client";

/**
 * Send a chat message to the AI Fashion Assistant.
 * Maps frontend message format { type, text } → backend { role, text }.
 */
export function sendChatMessage(message, history = []) {
  const mappedHistory = history.map((msg) => ({
    role: msg.type === "ai" ? "ai" : "user",
    text: msg.text,
  }));

  return api.post("/api/assistant/chat", {
    session_id: getSessionId(),
    message,
    history: mappedHistory,
  });
}
