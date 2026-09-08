import { NavLink } from "react-router-dom";
import "./SectionNav.css";

const LINKS = [
  { to: "/", label: "Feed", end: true },
  { to: "/models", label: "Models" },
  { to: "/companies", label: "Companies" },
  { to: "/pioneers", label: "Pioneers" },
  { to: "/leaderboard", label: "Leaderboard" },
];

export default function SectionNav() {
  return (
    <header className="nav">
      <div className="nav__inner">
        <div className="nav__brand">
          <svg className="nav__logo" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
            <defs>
              <linearGradient id="navLogoGradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                <stop offset="0%" style={{ stopColor: "var(--accent)" }} />
                <stop offset="100%" style={{ stopColor: "var(--cyan)" }} />
              </linearGradient>
            </defs>
            <rect width="32" height="32" rx="9" fill="url(#navLogoGradient)" />
            <path
              d="M16 16 8 10M16 16 24 10M16 16 8 22M16 16 24 22"
              stroke="var(--bg)"
              strokeWidth="1.6"
              strokeLinecap="round"
              opacity="0.9"
            />
            <circle cx="16" cy="16" r="3.4" fill="var(--bg)" />
            <circle cx="8" cy="10" r="2.1" fill="var(--bg)" />
            <circle cx="24" cy="10" r="2.1" fill="var(--bg)" />
            <circle cx="8" cy="22" r="2.1" fill="var(--bg)" />
            <circle cx="24" cy="22" r="2.1" fill="var(--bg)" />
          </svg>
          AI News
        </div>
        <nav className="nav__links">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `nav__link${isActive ? " nav__link--active" : ""}`}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
