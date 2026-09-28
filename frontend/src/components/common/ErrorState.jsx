export default function ErrorState({ message, onRetry }) {
  return (
    <div className="state-block error-state" role="alert">
      <p className="error-text">{message || "Something went wrong. Please try again."}</p>
      {onRetry ? (
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}
