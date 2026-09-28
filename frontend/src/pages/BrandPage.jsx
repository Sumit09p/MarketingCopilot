import { useEffect, useMemo, useState } from "react";
import BrandForm from "../components/brand/BrandForm";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import { brandService } from "../services";
import { getUserFacingError } from "../utils/errors";

function emptyForm() {
  return {
    company_name: "",
    industry: "",
    website: "",
    description: "",
    location: "",
    target_audience: {
      age_range: "",
      locations: [],
      interests: [],
      pain_points: [],
    },
    brand_voice: "",
    brand_tone: "",
    usp: "",
    products_services: [],
    competitors: [],
    marketing_goals: [],
  };
}

function fromApi(data) {
  const base = emptyForm();
  if (!data || typeof data !== "object") return base;
  const audience = data.target_audience && typeof data.target_audience === "object" ? data.target_audience : {};
  return {
    ...base,
    company_name: data.company_name ?? "",
    industry: data.industry ?? "",
    website: data.website ?? "",
    description: data.description ?? "",
    location: data.location ?? "",
    target_audience: {
      age_range: audience.age_range ?? "",
      locations: Array.isArray(audience.locations) ? audience.locations : [],
      interests: Array.isArray(audience.interests) ? audience.interests : [],
      pain_points: Array.isArray(audience.pain_points) ? audience.pain_points : [],
    },
    brand_voice: data.brand_voice ?? "",
    brand_tone: data.brand_tone ?? "",
    usp: data.usp ?? "",
    products_services: Array.isArray(data.products_services) ? data.products_services : [],
    competitors: Array.isArray(data.competitors) ? data.competitors : [],
    marketing_goals: Array.isArray(data.marketing_goals) ? data.marketing_goals : [],
  };
}

function toPayload(form) {
  return {
    company_name: form.company_name.trim(),
    industry: form.industry.trim(),
    website: form.website.trim(),
    description: form.description.trim(),
    location: form.location.trim(),
    target_audience: {
      age_range: form.target_audience.age_range.trim(),
      locations: form.target_audience.locations,
      interests: form.target_audience.interests,
      pain_points: form.target_audience.pain_points,
    },
    brand_voice: form.brand_voice.trim(),
    brand_tone: form.brand_tone.trim(),
    usp: form.usp.trim(),
    products_services: form.products_services,
    competitors: form.competitors,
    marketing_goals: form.marketing_goals,
  };
}

function validate(form) {
  const errors = {};
  if (!form.company_name.trim()) errors.company_name = "Company name is required.";
  if (!form.industry.trim()) errors.industry = "Industry is required.";
  if (form.website.trim()) {
    try {
      const parsed = new URL(form.website.trim());
      if (!["http:", "https:"].includes(parsed.protocol)) errors.website = "Website must start with http:// or https://.";
    } catch {
      errors.website = "Enter a valid website URL.";
    }
  }
  return errors;
}

export default function BrandPage() {
  const [status, setStatus] = useState("loading");
  const [form, setForm] = useState(emptyForm);
  const [snapshot, setSnapshot] = useState(emptyForm);
  const [errors, setErrors] = useState({});
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadBrand() {
    setStatus("loading");
    setLoadError("");
    try {
      const data = await brandService.getBrand();
      const next = fromApi(data);
      setForm(next);
      setSnapshot(next);
      setStatus("ready");
    } catch (err) {
      setLoadError(getUserFacingError(err, "Could not load the brand profile."));
      setStatus("error");
    }
  }

  useEffect(() => {
    loadBrand();
  }, []);

  const dirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(snapshot), [form, snapshot]);
  const isEmptyProfile = !snapshot.company_name && !snapshot.industry && !snapshot.description;

  function onChange(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setSaveSuccess("");
    setSaveError("");
  }

  function onAudienceChange(field, value) {
    setForm((current) => ({
      ...current,
      target_audience: { ...current.target_audience, [field]: value },
    }));
    setSaveSuccess("");
    setSaveError("");
  }

  async function onSubmit(event) {
    event.preventDefault();
    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setSaveError("Please fix the highlighted fields.");
      setSaveSuccess("");
      return;
    }

    setSubmitting(true);
    setSaveError("");
    setSaveSuccess("");
    try {
      await brandService.updateBrand(toPayload(form));
      const saved = toPayload(form);
      setForm(fromApi(saved));
      setSnapshot(fromApi(saved));
      setSaveSuccess("Brand profile saved.");
    } catch (err) {
      setSaveError(getUserFacingError(err, "Could not save the brand profile."));
    } finally {
      setSubmitting(false);
    }
  }

  function onCancel() {
    setForm(snapshot);
    setErrors({});
    setSaveError("");
    setSaveSuccess("");
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Brand profile"
        description="Keep company, audience, and voice details current so campaign agents have the right context."
      />

      {status === "loading" ? <LoadingState message="Loading brand profile..." /> : null}
      {status === "error" ? <ErrorState message={loadError} onRetry={loadBrand} /> : null}

      {status === "ready" ? (
        <div className="page-card">
          {isEmptyProfile ? (
            <EmptyState
              title="No brand details yet"
              description="Fill in the profile below. This information is stored through the brand API and used across the workspace."
            />
          ) : null}
          {saveSuccess ? <p className="success-text">{saveSuccess}</p> : null}
          {saveError ? <p className="error-text">{saveError}</p> : null}
          <BrandForm
            form={form}
            errors={errors}
            onChange={onChange}
            onAudienceChange={onAudienceChange}
            onSubmit={onSubmit}
            onCancel={onCancel}
            submitting={submitting}
            dirty={dirty}
          />
        </div>
      ) : null}
    </section>
  );
}
