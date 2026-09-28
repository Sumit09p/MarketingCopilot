export default function MessageBubble({ role, content }) {
  return (
    <article className={`message-bubble ${role}`}>
      <span className="message-role">{role}</span>
      {content}
    </article>
  );
}
