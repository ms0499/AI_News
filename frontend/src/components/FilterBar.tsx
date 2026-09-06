import "./FilterBar.css";

const SECTIONS: { value: string | null; label: string }[] = [
  { value: null, label: "All" },
  { value: "news", label: "News" },
  { value: "models", label: "Models" },
  { value: "companies", label: "Companies" },
  { value: "papers", label: "Papers" },
];

interface Props {
  section: string | null;
  onSectionChange: (section: string | null) => void;
  activeFilters: { company?: string; topic?: string };
  onClearFilter: (kind: "company" | "topic") => void;
}

export default function FilterBar({ section, onSectionChange, activeFilters, onClearFilter }: Props) {
  return (
    <div className="filterbar">
      <div className="filterbar__sections">
        {SECTIONS.map((s) => (
          <button
            key={s.label}
            className={`filterbar__tab${section === s.value ? " filterbar__tab--active" : ""}`}
            onClick={() => onSectionChange(s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {(activeFilters.company || activeFilters.topic) && (
        <div className="filterbar__active">
          {activeFilters.company && (
            <span className="chip chip--company" onClick={() => onClearFilter("company")}>
              {activeFilters.company} ×
            </span>
          )}
          {activeFilters.topic && (
            <span className="chip chip--active" onClick={() => onClearFilter("topic")}>
              #{activeFilters.topic} ×
            </span>
          )}
        </div>
      )}
    </div>
  );
}
