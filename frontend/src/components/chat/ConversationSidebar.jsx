export default function ConversationSidebar({ conversations, activeId }) {
  return (
    <aside className="conversation-pane">
      <h2>Conversations</h2>
      {conversations.length === 0 ? (
        <p className="muted">No conversations yet.</p>
      ) : (
        conversations.map((item) => (
          <div key={item.id} className={`conversation-item${item.id === activeId ? " active" : ""}`}>
            {item.title}
          </div>
        ))
      )}
    </aside>
  );
}
