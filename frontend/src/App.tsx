import { Route, Routes } from "react-router-dom";
import SectionNav from "./components/SectionNav";
import Feed from "./pages/Feed";
import Models from "./pages/Models";
import Companies from "./pages/Companies";
import CompanyDetail from "./pages/CompanyDetail";
import Pioneers from "./pages/Pioneers";
import Leaderboard from "./pages/Leaderboard";
import "./App.layout.css";

export default function App() {
  return (
    <div className="app">
      <SectionNav />
      <main className="app__main">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/models" element={<Models />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:slug" element={<CompanyDetail />} />
          <Route path="/pioneers" element={<Pioneers />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </main>
    </div>
  );
}
