const PLATFORM_OPTIONS = ["Instagram", "LinkedIn", "Facebook", "YouTube", "X"];

function Field({ id, label, error, children }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {children}
      {error ? <span className="field-error">{error}</span> : null}
    </div>
  );
}

export default function CampaignForm({ form, errors, onChange, onPlatformToggle, onSubmit, submitting }) {
  return (
    <form className="stack-form" onSubmit={onSubmit} noValidate>
      <div className="form-grid">
        <Field id="name" label="Campaign name" error={errors.name}>
          <input id="name" value={form.name} onChange={(event) => onChange("name", event.target.value)} />
        </Field>
        <Field id="objective" label="Objective" error={errors.objective}>
          <input
            id="objective"
            value={form.objective}
            onChange={(event) => onChange("objective", event.target.value)}
            placeholder="Awareness, leads, sales..."
          />
        </Field>
        <Field id="product" label="Product" error={errors.product}>
          <input id="product" value={form.product} onChange={(event) => onChange("product", event.target.value)} />
        </Field>
        <Field id="audience" label="Audience" error={errors.audience}>
          <input id="audience" value={form.audience} onChange={(event) => onChange("audience", event.target.value)} />
        </Field>
        <Field id="budget" label="Budget" error={errors.budget}>
          <input
            id="budget"
            type="number"
            min="0"
            step="1"
            value={form.budget}
            onChange={(event) => onChange("budget", event.target.value)}
          />
        </Field>
      </div>

      <fieldset className="form-field">
        <legend>Platforms</legend>
        <div className="choice-row">
          {PLATFORM_OPTIONS.map((platform) => (
            <label key={platform} className="choice-chip">
              <input
                type="checkbox"
                checked={form.platforms.includes(platform)}
                onChange={() => onPlatformToggle(platform)}
              />
              {platform}
            </label>
          ))}
        </div>
        {errors.platforms ? <span className="field-error">{errors.platforms}</span> : null}
      </fieldset>

      <div className="form-grid">
        <Field id="duration_start" label="Start date" error={errors.start}>
          <input
            id="duration_start"
            type="date"
            value={form.duration.start}
            onChange={(event) => onChange("duration", { ...form.duration, start: event.target.value })}
          />
        </Field>
        <Field id="duration_end" label="End date" error={errors.end}>
          <input
            id="duration_end"
            type="date"
            value={form.duration.end}
            onChange={(event) => onChange("duration", { ...form.duration, end: event.target.value })}
          />
        </Field>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? "Creating..." : "Create campaign"}
        </button>
      </div>
    </form>
  );
}
