import "./StateNotice.css";

export default function StateNotice({ kind, message }: { kind: "loading" | "error" | "empty"; message: string }) {
  return (
    <div className={`notice notice--${kind}`}>
      {kind === "loading" && <span className="notice__spinner" />}
      {message}
    </div>
  );
}
