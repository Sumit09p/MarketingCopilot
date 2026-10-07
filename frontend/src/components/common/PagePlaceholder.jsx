export default function PagePlaceholder({ title, description }) {
  return (
    <section className="page-card">
      <h1>{title}</h1>
      <p>{description}</p>
    </section>
  );
}
