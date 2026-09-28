export default function ConversationSidebar({
  conversations,
  activeId,
  renamingId,
  renameValue,
  onRenameValueChange,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onSelect,
  onNewChat,
  onDelete,
  disabled,
}) {
  return (
    <aside className="conversation-pane">
      <div className="conversation-pane-header">
        <h2>Conversations</h2>
        <button type="button" className="btn btn-secondary" onClick={onNewChat} disabled={disabled}>
          New Chat
        </button>
      </div>
      {conversations.length === 0 ? (
        <p className="muted">No conversations yet. Start a new chat to begin.</p>
      ) : (
        <ul className="conversation-list">
          {conversations.map((item) => {
            const isActive = item.id === activeId;
            const isRenaming = renamingId === item.id;
            return (
              <li key={item.id} className={`conversation-item${isActive ? " active" : ""}`}>
                {isRenaming ? (
                  <form
                    className="conversation-rename"
                    onSubmit={(event) => {
                      event.preventDefault();
                      onSaveRename(item.id);
                    }}
                  >
                    <label className="visually-hidden" htmlFor={`rename-${item.id}`}>
                      Conversation title
                    </label>
                    <input
                      id={`rename-${item.id}`}
                      value={renameValue}
                      onChange={(event) => onRenameValueChange(event.target.value)}
                      autoFocus
                    />
                    <div className="conversation-actions">
                      <button className="btn" type="submit">
                        Save
                      </button>
                      <button className="btn btn-secondary" type="button" onClick={onCancelRename}>
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <button
                      type="button"
                      className="conversation-select"
                      onClick={() => onSelect(item.id)}
                      disabled={disabled}
                    >
                      {item.title}
                    </button>
                    <div className="conversation-actions">
                      <button type="button" className="btn-link" onClick={() => onStartRename(item)} disabled={disabled}>
                        Rename
                      </button>
                      <button type="button" className="btn-link danger" onClick={() => onDelete(item)} disabled={disabled}>
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
