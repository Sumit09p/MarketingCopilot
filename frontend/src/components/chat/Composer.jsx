export default function Composer({ value, onChange, onSend, disabled }) {
  function handleSubmit(event) {
    event.preventDefault();
    if (disabled) return;
    const text = (value || "").trim();
    if (!text) return;
    onSend(text);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <label className="visually-hidden" htmlFor="composer-input">
        Message to MarketingOS AI
      </label>
      <textarea
        id="composer-input"
        rows={2}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask MarketingOS anything..."
        disabled={disabled}
      />
      <button className="btn" type="submit" disabled={disabled || !(value || "").trim()}>
        Send
      </button>
    </form>
  );
}
