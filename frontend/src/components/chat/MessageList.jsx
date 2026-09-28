import MessageBubble from "./MessageBubble";

export default function MessageList({ messages }) {
  if (!messages.length) {
    return (
      <div className="message-list">
        <p className="muted">Message list foundation. Full chat comes in a later module.</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageBubble key={message.id} role={message.role} content={message.content} />
      ))}
    </div>
  );
}
