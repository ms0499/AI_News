import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import "./SectionNav.css";

type IconProps = { className?: string };

const FeedIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
    <rect x="3" y="4" width="18" height="16" rx="2.5" stroke="currentColor" strokeWidth="1.7" />
    <path d="M7 8h7M7 12h10M7 16h6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
  </svg>
);

const ModelsIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
    <path
      d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinejoin="round"
    />
    <path d="M4 7.5l8 4.5 8-4.5M12 12v9" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
  </svg>
);

const CompaniesIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
    <rect x="4" y="3" width="10" height="18" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
    <path d="M14 9h6v12h-6" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
    <path
      d="M7 7h4M7 11h4M7 15h4M17 13h0M17 17h0"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
    />
  </svg>
);

const PioneersIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
    <circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.7" />
    <path d="M3.5 19a5.5 5.5 0 0111 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    <path
      d="M16 5.4a3.2 3.2 0 010 5.2M17.5 19a5.5 5.5 0 00-3-4.9"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
    />
  </svg>
);

const LeaderboardIcon = ({ className }: IconProps) => (
  <svg className={className} viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
    <path d="M5 20h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    <rect x="5" y="11" width="4" height="6" rx="1" stroke="currentColor" strokeWidth="1.7" />
    <rect x="10" y="6" width="4" height="11" rx="1" stroke="currentColor" strokeWidth="1.7" />
    <rect x="15" y="14" width="4" height="3" rx="1" stroke="currentColor" strokeWidth="1.7" />
  </svg>
);

type NavItem = { to: string; label: string; end?: boolean; icon: (props: IconProps) => ReactNode };

const LINKS: NavItem[] = [
  { to: "/", label: "Feed", end: true, icon: FeedIcon },
  { to: "/models", label: "Models", icon: ModelsIcon },
  { to: "/companies", label: "Companies", icon: CompaniesIcon },
  { to: "/pioneers", label: "Pioneers", icon: PioneersIcon },
  { to: "/leaderboard", label: "Leaderboard", icon: LeaderboardIcon },
];

export default function SectionNav() {
  return (
    <>
      <header className="nav">
        <div className="nav__inner">
          <Link to="/" className="nav__brand" aria-label="AI News home">
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
          </Link>
          <nav className="nav__links" aria-label="Primary">
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

      {/* Mobile bottom tab bar — thumb-reachable, always accessible. */}
      <nav className="mobnav" aria-label="Primary">
        {LINKS.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `mobnav__link${isActive ? " mobnav__link--active" : ""}`}
            >
              <Icon className="mobnav__icon" />
              <span className="mobnav__label">{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </>
  );
}
