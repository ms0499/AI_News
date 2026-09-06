import { NavLink } from "react-router-dom";
import "./SectionNav.css";

const LINKS = [
  { to: "/", label: "Feed", end: true },
  { to: "/models", label: "Models" },
  { to: "/companies", label: "Companies" },
];

export default function SectionNav() {
  return (
    <header className="nav">
      <div className="nav__inner">
        <div className="nav__brand">
          <span className="nav__brand-mark" />
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
