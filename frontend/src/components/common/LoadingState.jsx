export default function LoadingState({ message = "Loading..." }) {
  return (
    <div className="state-block" role="status">
      <p className="muted">{message}</p>
    </div>
  );
}
