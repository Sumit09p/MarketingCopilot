import MessageBubble from "./MessageBubble";

const EXAMPLE_PROMPTS = [
  "Create a social media campaign for my product",
  "Research competitors in my industry",
  "Find SEO keywords for my website",
  "Create Instagram captions for my campaign",
];

export default function MessageList({
  messages,
  loading,
  sending,
  onExampleClick,
}) {
  if (loading) {
    return (
      <div className="message-list">
        <p className="muted">Loading messages...</p>
      </div>
    );
  }

  if (!messages.length && !sending) {
    return (
      <div className="message-list welcome-state">
        <div className="welcome-copy">
          <p className="welcome-kicker">✦ Ask PRISM</p>
          <h2>How can I help with your marketing?</h2>
          <p className="muted">Choose an example or type your own question. Examples fill the composer and do not send automatically.</p>
        </div>
        <div className="example-prompts">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="example-prompt"
              onClick={() => onExampleClick(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <MessageBubble key={message.id} role={message.role} content={message.content} />
      ))}
      {sending ? (
        <div className="message-row assistant">
          <img className="message-avatar prism-message-avatar" src="/brand/prism-icon.png" alt="" aria-hidden="true" />
          <article className="message-bubble assistant typing" aria-live="polite">
            <span className="message-role">PRISM</span>
            <p className="message-content">PRISM is thinking...</p>
          </article>
        </div>
      ) : null}
    </div>
  );
}
