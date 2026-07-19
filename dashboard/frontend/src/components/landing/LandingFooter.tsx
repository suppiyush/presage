import { Link } from "react-router-dom";

export default function LandingFooter() {
  return (
    <footer className="flex items-center justify-between border-t border-sand px-10 py-6.5 text-[13px] text-dune">
      <span>Presage — a hackathon project by Team Parity Check, 2026</span>
      <div className="flex gap-5.5">
        <a href="#product" className="text-clay hover:text-flame">Product</a>
        <a href="#contact" className="text-clay hover:text-flame">Contact</a>
        <Link to="/dashboard" className="text-clay hover:text-flame">Dashboard</Link>
      </div>
    </footer>
  );
}
