export default function Composer() {
  return (
    <form className="composer" onSubmit={(event) => event.preventDefault()}>
      <label className="visually-hidden" htmlFor="composer-input">
        Message
      </label>
      <textarea id="composer-input" placeholder="Message input foundation — sending is not implemented yet." disabled />
      <button type="submit" className="btn" disabled>
        Send
      </button>
    </form>
  );
}
