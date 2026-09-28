import { useEffect, useState } from "react";
import AgentSelector from "../components/chat/AgentSelector";
import Composer from "../components/chat/Composer";
import ConversationSidebar from "../components/chat/ConversationSidebar";
import MessageList from "../components/chat/MessageList";
import { conversationsService } from "../services";

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    conversationsService
      .listConversations()
      .then(async (items) => {
        if (cancelled) return;
        setConversations(items);
        const first = items[0];
        if (!first) return;
        setActiveId(first.id);
        const detail = await conversationsService.getConversation(first.id);
        if (!cancelled) setMessages(detail.messages ?? []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Could not load conversations");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="chat-layout">
      <ConversationSidebar conversations={conversations} activeId={activeId} />
      <section className="chat-pane chat-main">
        <div className="chat-toolbar">
          <div>
            <strong>Chat foundation</strong>
            <p className="muted" style={{ margin: 0 }}>
              Layout only. Sending messages is not implemented yet.
            </p>
          </div>
          <AgentSelector />
        </div>
        {error ? <p className="error-text" style={{ padding: "0 16px" }}>{error}</p> : null}
        <MessageList messages={messages} />
        <Composer />
      </section>
    </div>
  );
}
