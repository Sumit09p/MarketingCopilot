import ArrayField from "../common/ArrayField";

function Field({ id, label, error, children }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {children}
      {error ? <span className="field-error">{error}</span> : null}
    </div>
  );
}

export default function BrandForm({
  form,
  errors,
  onChange,
  onAudienceChange,
  onSubmit,
  onCancel,
  submitting,
  dirty,
}) {
  return (
    <form className="stack-form" onSubmit={onSubmit} noValidate>
      <div className="form-grid">
        <Field id="company_name" label="Company" error={errors.company_name}>
          <input
            id="company_name"
            value={form.company_name}
            onChange={(event) => onChange("company_name", event.target.value)}
          />
        </Field>
        <Field id="industry" label="Industry" error={errors.industry}>
          <input id="industry" value={form.industry} onChange={(event) => onChange("industry", event.target.value)} />
        </Field>
        <Field id="website" label="Website" error={errors.website}>
          <input
            id="website"
            type="url"
            placeholder="https://example.com"
            value={form.website}
            onChange={(event) => onChange("website", event.target.value)}
          />
        </Field>
        <Field id="location" label="Location">
          <input id="location" value={form.location} onChange={(event) => onChange("location", event.target.value)} />
        </Field>
      </div>

      <Field id="description" label="Description">
        <textarea
          id="description"
          rows={4}
          value={form.description}
          onChange={(event) => onChange("description", event.target.value)}
        />
      </Field>

      <h2 className="section-title">Target audience</h2>
      <div className="form-grid">
        <Field id="age_range" label="Age range">
          <input
            id="age_range"
            value={form.target_audience.age_range}
            onChange={(event) => onAudienceChange("age_range", event.target.value)}
          />
        </Field>
      </div>
      <ArrayField
        id="audience_locations"
        label="Audience locations"
        values={form.target_audience.locations}
        onChange={(value) => onAudienceChange("locations", value)}
        placeholder="Add a location"
      />
      <ArrayField
        id="audience_interests"
        label="Interests"
        values={form.target_audience.interests}
        onChange={(value) => onAudienceChange("interests", value)}
        placeholder="Add an interest"
      />
      <ArrayField
        id="audience_pain_points"
        label="Pain points"
        values={form.target_audience.pain_points}
        onChange={(value) => onAudienceChange("pain_points", value)}
        placeholder="Add a pain point"
      />

      <div className="form-grid">
        <Field id="brand_voice" label="Voice">
          <input
            id="brand_voice"
            value={form.brand_voice}
            onChange={(event) => onChange("brand_voice", event.target.value)}
          />
        </Field>
        <Field id="brand_tone" label="Tone">
          <input
            id="brand_tone"
            value={form.brand_tone}
            onChange={(event) => onChange("brand_tone", event.target.value)}
          />
        </Field>
      </div>

      <Field id="usp" label="USP">
        <textarea id="usp" rows={3} value={form.usp} onChange={(event) => onChange("usp", event.target.value)} />
      </Field>

      <ArrayField
        id="products_services"
        label="Products"
        values={form.products_services}
        onChange={(value) => onChange("products_services", value)}
        placeholder="Add a product or service"
      />
      <ArrayField
        id="competitors"
        label="Competitors"
        values={form.competitors}
        onChange={(value) => onChange("competitors", value)}
        placeholder="Add a competitor"
      />
      <ArrayField
        id="marketing_goals"
        label="Goals"
        values={form.marketing_goals}
        onChange={(value) => onChange("marketing_goals", value)}
        placeholder="Add a goal"
      />

      <div className="form-actions">
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? "Saving..." : "Save profile"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={submitting || !dirty}>
          Cancel
        </button>
      </div>
    </form>
  );
}
