import { delay } from "./delay";
import conversationsData from "./data/conversations.json";
import messagesData from "./data/messages.json";
import { ApiError } from "../services/apiClient";

const conversations = conversationsData.map((item) => ({ ...item }));
const messagesByConversation = JSON.parse(JSON.stringify(messagesData));

export async function listConversations() {
  await delay();
  return conversations.map((item) => ({ ...item }));
}

export async function getConversation(conversationId) {
  await delay();
  const conversation = conversations.find((item) => item.id === conversationId);
  if (!conversation) {
    throw new ApiError("Resource not found", { status: 404, data: null });
  }
  return {
    ...conversation,
    messages: (messagesByConversation[conversationId] ?? []).map((item) => ({ ...item })),
  };
}

export async function createConversation({ title }) {
  await delay();
  const conversation = {
    id: `conversation_${Date.now()}`,
    title: title || "New conversation",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  conversations.unshift(conversation);
  messagesByConversation[conversation.id] = [];
  return { id: conversation.id, title: conversation.title };
}

export async function renameConversation(conversationId, { title }) {
  await delay();
  const conversation = conversations.find((item) => item.id === conversationId);
  if (!conversation) {
    throw new ApiError("Resource not found", { status: 404, data: null });
  }
  conversation.title = title;
  conversation.updated_at = new Date().toISOString();
  return { id: conversation.id, title: conversation.title };
}

export async function deleteConversation(conversationId) {
  await delay();
  const index = conversations.findIndex((item) => item.id === conversationId);
  if (index >= 0) conversations.splice(index, 1);
  delete messagesByConversation[conversationId];
  return null;
}

export { messagesByConversation, conversations };
