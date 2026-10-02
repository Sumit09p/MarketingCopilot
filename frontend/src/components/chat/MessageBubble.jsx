export default function MessageBubble({ role, content }) {
  const isUser = role === "user";
  const label = isUser ? "You" : "PRISM";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      {!isUser ? <img className="message-avatar prism-message-avatar" src="/brand/prism-icon.png" alt="" aria-hidden="true" /> : null}
      <article className={`message-bubble ${role}`}>
        <span className="message-role">{label}</span>
        <p className="message-content">{content}</p>
      </article>
      {isUser ? (
        <span className="message-avatar user-message-avatar" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="8" r="3.25" />
            <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
          </svg>
        </span>
      ) : null}
    </div>
  );
}
