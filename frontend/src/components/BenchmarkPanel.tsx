import { BENCHMARK_AS_OF, BENCHMARK_MODELS } from "../data/benchmarks";
import "./BenchmarkPanel.css";

const RANK_MEDAL = ["🥇", "🥈", "🥉"];

export default function BenchmarkPanel() {
  const top = BENCHMARK_MODELS[0]?.index ?? 100;

  return (
    <aside className="benchmark-panel">
      <div className="benchmark-panel__header">
        <h2>Model Benchmarks</h2>
        <p>Frontier models ranked by composite intelligence index</p>
      </div>

      <ol className="benchmark-panel__list">
        {BENCHMARK_MODELS.map((m, i) => (
          <li className="benchmark-row" key={m.model} data-rank={i + 1}>
            <div className="benchmark-row__top">
              <span className="benchmark-row__rank">{RANK_MEDAL[i] ?? `#${i + 1}`}</span>
              <span className="benchmark-row__name">
                {m.model}
                <span className="benchmark-row__company">{m.company}</span>
              </span>
              <span className="benchmark-row__score">{m.index}</span>
            </div>

            <div
              className="benchmark-row__bar"
              role="img"
              aria-label={`${m.model} intelligence index ${m.index} out of 100`}
            >
              <span
                className="benchmark-row__fill"
                style={{ width: `${(m.index / top) * 100}%` }}
              />
            </div>

            <div className="benchmark-row__subs">
              <span className="benchmark-sub">
                <span className="benchmark-sub__label">Reasoning</span>
                <span className="benchmark-sub__track">
                  <span
                    className="benchmark-sub__fill benchmark-sub__fill--reason"
                    style={{ width: `${m.reasoning}%` }}
                  />
                </span>
                <span className="benchmark-sub__val">{m.reasoning}</span>
              </span>
              <span className="benchmark-sub">
                <span className="benchmark-sub__label">Coding</span>
                <span className="benchmark-sub__track">
                  <span
                    className="benchmark-sub__fill benchmark-sub__fill--code"
                    style={{ width: `${m.coding}%` }}
                  />
                </span>
                <span className="benchmark-sub__val">{m.coding}</span>
              </span>
            </div>
          </li>
        ))}
      </ol>

      <p className="benchmark-panel__footer">
        Curated snapshot · {BENCHMARK_AS_OF}. Composite of public reasoning &amp; coding
        benchmarks — verify &amp; edit in <code>data/benchmarks.ts</code>.
      </p>
    </aside>
  );
}
