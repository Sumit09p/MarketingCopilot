export default function MessageBubble({ role, content }) {
  const label = role === "user" ? "You" : "MarketingOS AI";

  return (
    <article className={`message-bubble ${role}`}>
      <span className="message-role">{label}</span>
      <p className="message-content">{content}</p>
    </article>
  );
}
