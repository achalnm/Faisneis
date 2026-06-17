export default function TricolourStripe() {
  return (
    <div className="flex w-full" style={{ height: 3 }} aria-hidden="true">
      <div className="flex-1" style={{ background: "#169B62" }} />
      <div className="flex-1" style={{ background: "#ffffff" }} />
      <div className="flex-1" style={{ background: "#FF883E" }} />
    </div>
  );
}
