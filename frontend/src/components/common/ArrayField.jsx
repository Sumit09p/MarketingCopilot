import { useState } from "react";

export default function ArrayField({ id, label, values, onChange, placeholder = "Add an item" }) {
  const [draft, setDraft] = useState("");
  const items = Array.isArray(values) ? values : [];

  function addItem() {
    const next = draft.trim();
    if (!next) return;
    onChange([...items, next]);
    setDraft("");
  }

  function removeItem(index) {
    onChange(items.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="chip-list">
        {items.length === 0 ? <span className="muted">None added yet.</span> : null}
        {items.map((item, index) => (
          <span key={`${item}-${index}`} className="chip">
            {item}
            <button type="button" className="chip-remove" onClick={() => removeItem(index)} aria-label={`Remove ${item}`}>
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="inline-add">
        <input
          id={id}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addItem();
            }
          }}
          placeholder={placeholder}
        />
        <button type="button" className="btn btn-secondary" onClick={addItem}>
          Add
        </button>
      </div>
    </div>
  );
}
