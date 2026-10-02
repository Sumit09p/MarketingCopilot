import { useCallback, useEffect, useRef, useState } from "react";
import AgentSelector from "../components/chat/AgentSelector";
import Composer from "../components/chat/Composer";
import ConversationSidebar from "../components/chat/ConversationSidebar";
import MessageList from "../components/chat/MessageList";
import { ApiError } from "../services/apiClient";
import { chatService, conversationsService } from "../services";
import { getUserFacingError } from "../utils/errors";

function titleFromMessage(text) {
  const trimmed = text.trim().replace(/\s+/g, " ");
  if (trimmed.length <= 48) return trimmed;
  return `${trimmed.slice(0, 45)}...`;
}

function nextLocalId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [agent, setAgent] = useState("");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [failedAttempt, setFailedAttempt] = useState(null);
  const loadToken = useRef(0);

  const refreshConversations = useCallback(async () => {
    const items = await conversationsService.listConversations();
    setConversations(items);
    return items;
  }, []);

  useEffect(() => {
    let cancelled = false;
    setListLoading(true);
    refreshConversations()
      .catch((err) => {
        if (!cancelled) setError(getUserFacingError(err, "Could not load conversations."));
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshConversations]);

  async function selectConversation(id) {
    const token = ++loadToken.current;
    setActiveId(id);
    setError("");
    setFailedAttempt(null);
    setMessagesLoading(true);
    try {
      const detail = await conversationsService.getConversation(id);
      if (token !== loadToken.current) return;
      setMessages(detail.messages ?? []);
    } catch (err) {
      if (token !== loadToken.current) return;
      setMessages([]);
      setError(getUserFacingError(err, "Could not load that conversation."));
    } finally {
      if (token === loadToken.current) setMessagesLoading(false);
    }
  }

  function startNewChat() {
    loadToken.current += 1;
    setActiveId(null);
    setMessages([]);
    setError("");
    setFailedAttempt(null);
    setMessagesLoading(false);
    setRenamingId(null);
  }

  async function ensureConversation(text) {
    if (activeId) return activeId;
    const created = await conversationsService.createConversation({
      title: titleFromMessage(text) || "New Marketing Campaign",
    });
    setActiveId(created.id);
    setConversations((current) => [
      { id: created.id, title: created.title, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      ...current.filter((item) => item.id !== created.id),
    ]);
    return created.id;
  }

  async function send(text, { isRetry = false } = {}) {
    const message = text.trim();
    if (!message || sending) return;

    setError("");
    setSending(true);
    setFailedAttempt(null);

    if (!isRetry) {
      setMessages((current) => [
        ...current,
        {
          id: nextLocalId("local_user"),
          role: "user",
          content: message,
          created_at: new Date().toISOString(),
        },
      ]);
      setDraft("");
    }

    try {
      const conversationId = await ensureConversation(message);

      if (agent) {
        const result = await chatService.sendAgentMessage({
          agent,
          message,
          conversation_id: conversationId,
        });

        if (result?.guardrail === "NEEDS_CLARIFICATION") {
          setMessages((current) => [
            ...current,
            {
              id: nextLocalId("clarify"),
              role: "assistant",
              content: result.question || "Could you provide a bit more detail?",
              created_at: new Date().toISOString(),
            },
          ]);
          setFailedAttempt(null);
          return;
        }

        const detail = await conversationsService.getConversation(conversationId);
        setMessages(detail.messages ?? []);
        await refreshConversations();
        setFailedAttempt(null);
        return;
      }

      const result = await chatService.sendMessage({
        conversation_id: conversationId,
        message,
      });
      const resolvedId = result.conversation_id || conversationId;
      setActiveId(resolvedId);
      const detail = await conversationsService.getConversation(resolvedId);
      setMessages(detail.messages ?? []);
      await refreshConversations();
      setFailedAttempt(null);
    } catch (err) {
      const fallback = "Something went wrong while sending your message.";
      setFailedAttempt({ text: message, agent });
      if (err instanceof ApiError && err.data?.guardrail === "INVALID") {
        setMessages((current) => [
          ...current,
          {
            id: nextLocalId("invalid"),
            role: "assistant",
            content: err.message || fallback,
            created_at: new Date().toISOString(),
          },
        ]);
        setError("");
      } else {
        setError(getUserFacingError(err, fallback));
      }
    } finally {
      setSending(false);
    }
  }

  function startRename(conversation) {
    setRenamingId(conversation.id);
    setRenameValue(conversation.title);
  }

  async function saveRename(conversationId) {
    const title = renameValue.trim();
    if (!title) return;
    try {
      const updated = await conversationsService.renameConversation(conversationId, { title });
      setConversations((current) =>
        current.map((item) => (item.id === conversationId ? { ...item, title: updated.title } : item))
      );
      setRenamingId(null);
    } catch (err) {
      setError(getUserFacingError(err, "Could not rename that conversation."));
    }
  }

  async function deleteConversation(conversation) {
    const confirmed = window.confirm(`Delete “${conversation.title}”? This cannot be undone.`);
    if (!confirmed) return;
    try {
      await conversationsService.deleteConversation(conversation.id);
      setConversations((current) => current.filter((item) => item.id !== conversation.id));
      if (activeId === conversation.id) {
        startNewChat();
      }
    } catch (err) {
      setError(getUserFacingError(err, "Could not delete that conversation."));
    }
  }

  return (
    <div className="chat-layout">
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        renamingId={renamingId}
        renameValue={renameValue}
        onRenameValueChange={setRenameValue}
        onStartRename={startRename}
        onSaveRename={saveRename}
        onCancelRename={() => setRenamingId(null)}
        onSelect={selectConversation}
        onNewChat={startNewChat}
        onDelete={deleteConversation}
        disabled={sending || listLoading}
      />
      <section className="chat-pane chat-main">
        <div className="chat-toolbar">
          <div>
            <strong>{activeId ? "Conversation" : "New chat"}</strong>
            <p className="muted" style={{ margin: 0 }}>
              Ask PRISM for help, or choose a specialist for an explicit request.
            </p>
          </div>
          <AgentSelector value={agent} onChange={setAgent} disabled={sending} />
        </div>
        {error || failedAttempt ? (
          <div className="chat-error" role="alert">
            {error ? <p className="error-text">{error}</p> : <p className="muted">You can retry the last request.</p>}
            {failedAttempt && !sending ? (
              <button type="button" className="btn btn-secondary" onClick={() => send(failedAttempt.text, { isRetry: true })}>
                Retry
              </button>
            ) : null}
          </div>
        ) : null}
        <MessageList
          messages={messages}
          loading={messagesLoading}
          sending={sending}
          onExampleClick={setDraft}
        />
        <Composer value={draft} onChange={setDraft} onSend={(text) => send(text)} disabled={sending} />
      </section>
    </div>
  );
}
