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
        <button type="button" className="btn btn-secondary chat-new-button" onClick={onNewChat} disabled={disabled}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l-2 2v-6.5A7.5 7.5 0 1 1 20 11.5Z" />
            <path d="M12.5 8.5v6M9.5 11.5h6" />
          </svg>
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
