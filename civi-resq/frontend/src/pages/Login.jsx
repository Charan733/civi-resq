import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@civiresq.gov.in");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (e) {
      setError(e.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink-800 bg-contour p-4">
      <div className="bg-white rounded-lg p-7 w-full max-w-sm shadow-xl">
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-9 h-9 rounded-md bg-monsoon-500 flex items-center justify-center font-display font-bold text-lg text-white">
            C
          </div>
          <div>
            <div className="font-display font-semibold text-lg text-ink-800 leading-tight">CIVI-RESQ</div>
            <div className="text-[10px] font-mono text-ink-400 uppercase tracking-wider">Sign in</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ink-500 uppercase tracking-wide mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-ink-200 rounded-md px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-ink-500 uppercase tracking-wide mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-ink-200 rounded-md px-3 py-2 text-sm"
              required
            />
          </div>
          {error && <p className="text-xs text-risk-critical">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-monsoon-500 hover:bg-monsoon-600 text-white font-medium text-sm py-2.5 rounded-md disabled:opacity-50"
          >
            <LogIn size={15} /> {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-ink-100 text-xs text-ink-400 font-mono leading-relaxed">
          Demo accounts:
          <br />
          admin@civiresq.gov.in / Admin@12345
          <br />
          engineer@civiresq.gov.in / Engineer@12345
        </div>
      </div>
    </div>
  );
}
