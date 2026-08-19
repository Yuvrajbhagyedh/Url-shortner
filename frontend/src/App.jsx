import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import { useAuth } from "./lib/auth.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import LinkAnalytics from "./pages/LinkAnalytics.jsx";
import ApiKeys from "./pages/ApiKeys.jsx";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="center muted">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <header className="nav">
      <Link to="/" className="brand">
        Short<span>X</span>
      </Link>
      <nav>
        <Link to="/">Links</Link>
        <Link to="/keys">API Keys</Link>
      </nav>
      <div className="nav-right">
        <span className="muted">{user.email}</span>
        <button
          className="btn ghost"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Log out
        </button>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="app">
      <NavBar />
      <main className="container">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <Protected>
                <Dashboard />
              </Protected>
            }
          />
          <Route
            path="/analytics/:code"
            element={
              <Protected>
                <LinkAnalytics />
              </Protected>
            }
          />
          <Route
            path="/keys"
            element={
              <Protected>
                <ApiKeys />
              </Protected>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
