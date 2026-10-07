import { ApiError } from "../services/apiClient";
import { delay } from "./delay";
import { conversations, messagesByConversation } from "./conversations.mock";

function ensureConversation(conversationId) {
  if (conversationId) return conversationId;
  const created = {
    id: `conversation_${Date.now()}`,
    title: "New Marketing Campaign",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  conversations.unshift(created);
  messagesByConversation[created.id] = [];
  return created.id;
}

function appendMessages(conversationId, userText, assistantText) {
  const now = new Date().toISOString();
  const thread = messagesByConversation[conversationId] ?? [];
  const userMessage = {
    id: `message_${Date.now()}`,
    role: "user",
    content: userText,
    created_at: now,
  };
  const assistantMessage = {
    id: `message_${Date.now() + 1}`,
    role: "assistant",
    content: assistantText,
    created_at: now,
  };
  thread.push(userMessage, assistantMessage);
  messagesByConversation[conversationId] = thread;
  const conversation = conversations.find((item) => item.id === conversationId);
  if (conversation) conversation.updated_at = now;
  return assistantMessage;
}

export async function sendMessage({ conversation_id, message }) {
  await delay();
  const conversationId = ensureConversation(conversation_id);
  const reply = "I will create a marketing campaign...";
  const assistantMessage = appendMessages(conversationId, message, reply);
  return {
    conversation_id: conversationId,
    message_id: assistantMessage.id,
    response: reply,
    mode: "GENERAL",
    status: "COMPLETED",
  };
}

function looksLikeUrl(text) {
  return /https?:\/\/|www\./i.test(text);
}

export async function sendAgentMessage({ agent, message, conversation_id }) {
  await delay();
  const text = (message || "").toLowerCase();

  if (text.includes("capital of") || text.includes("birthday")) {
    throw new ApiError(`This request is not appropriate for the ${agent} Agent.`, {
      status: 400,
      data: { agent, guardrail: "INVALID" },
    });
  }

  if (agent === "seo" && !looksLikeUrl(message || "")) {
    return {
      agent,
      guardrail: "NEEDS_CLARIFICATION",
      question: "Please provide your website URL.",
    };
  }

  const conversationId = ensureConversation(conversation_id);
  appendMessages(conversationId, message, "Agent request accepted for later execution.");
  return {
    agent,
    guardrail: "VALID",
    status: "EXECUTING",
  };
}
