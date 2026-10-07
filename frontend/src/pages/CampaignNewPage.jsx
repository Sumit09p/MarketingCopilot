import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import CampaignForm from "../components/campaigns/CampaignForm";
import PageHeader from "../components/common/PageHeader";
import { campaignsService } from "../services";
import { getUserFacingError } from "../utils/errors";

function emptyForm() {
  return {
    name: "",
    objective: "",
    product: "",
    audience: "",
    platforms: [],
    budget: "",
    duration: { start: "", end: "" },
  };
}

function validate(form) {
  const errors = {};
  if (!form.name.trim()) errors.name = "Campaign name is required.";
  if (!form.objective.trim()) errors.objective = "Objective is required.";
  if (!form.product.trim()) errors.product = "Product is required.";
  if (!form.audience.trim()) errors.audience = "Audience is required.";
  if (!form.platforms.length) errors.platforms = "Select at least one platform.";
  if (form.budget === "" || form.budget === null) errors.budget = "Budget is required.";
  else if (Number(form.budget) < 0 || Number.isNaN(Number(form.budget))) errors.budget = "Enter a valid budget amount.";
  if (!form.duration.start) errors.start = "Start date is required.";
  if (!form.duration.end) errors.end = "End date is required.";
  if (form.duration.start && form.duration.end && form.duration.end < form.duration.start) {
    errors.end = "End date must be on or after the start date.";
  }
  return errors;
}

export default function CampaignNewPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function onChange(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setApiError("");
  }

  function onPlatformToggle(platform) {
    setForm((current) => {
      const has = current.platforms.includes(platform);
      return {
        ...current,
        platforms: has ? current.platforms.filter((item) => item !== platform) : [...current.platforms, platform],
      };
    });
    setApiError("");
  }

  async function onSubmit(event) {
    event.preventDefault();
    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      setApiError("Please complete the required fields.");
      return;
    }

    setSubmitting(true);
    setApiError("");
    try {
      const created = await campaignsService.createCampaign({
        name: form.name.trim(),
        objective: form.objective.trim(),
        product: form.product.trim(),
        audience: form.audience.trim(),
        platforms: form.platforms,
        budget: Number(form.budget),
        duration: {
          start: form.duration.start,
          end: form.duration.end,
        },
      });
      const id = created?.id;
      navigate(id ? `/campaigns/${id}` : "/campaigns");
    } catch (err) {
      setApiError(getUserFacingError(err, "Could not create the campaign."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Create campaign"
        description="Use only the campaign fields defined by the API contract."
        actions={
          <Link className="btn btn-secondary" to="/campaigns">
            Back to campaigns
          </Link>
        }
      />
      <div className="page-card">
        {apiError ? <p className="error-text">{apiError}</p> : null}
        <CampaignForm
          form={form}
          errors={errors}
          onChange={onChange}
          onPlatformToggle={onPlatformToggle}
          onSubmit={onSubmit}
          submitting={submitting}
        />
      </div>
    </section>
  );
}
