import { NavLink } from "react-router-dom";
import { LayoutDashboard, Map, Sliders, MessageSquareText, UploadCloud, LogIn, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/map", label: "Risk Map", icon: Map },
  { to: "/simulator", label: "What-If Simulator", icon: Sliders },
  { to: "/assistant", label: "CIVI-AI Assistant", icon: MessageSquareText },
  { to: "/upload", label: "Upload Data", icon: UploadCloud },
];

export default function Shell({ children }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Sidebar */}
      <aside className="bg-ink-800 text-paper-100 md:w-64 flex-shrink-0 md:min-h-screen md:flex md:flex-col">
        <div className="relative bg-contour px-5 py-6 border-b border-ink-600">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-md bg-monsoon-500 flex items-center justify-center font-display font-bold text-lg">
              C
            </div>
            <div>
              <div className="font-display font-semibold text-lg leading-tight tracking-tight">CIVI-RESQ</div>
              <div className="text-[10px] font-mono text-ink-300 tracking-widest uppercase">Risk & Intervention Planning</div>
            </div>
          </div>
        </div>
        <nav className="p-3 flex md:flex-col gap-1 overflow-x-auto md:overflow-visible">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-monsoon-600/40 text-white border-l-2 border-monsoon-400"
                    : "text-ink-200 hover:bg-ink-700 hover:text-white border-l-2 border-transparent"
                }`
              }
            >
              <Icon size={17} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto p-4 border-t border-ink-700">
          {user ? (
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="text-xs font-medium text-white truncate">{user.full_name}</div>
                <div className="text-[10px] font-mono text-ink-400 uppercase">{user.role}</div>
              </div>
              <button onClick={logout} className="text-ink-300 hover:text-white flex-shrink-0" title="Log out">
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <NavLink to="/login" className="flex items-center gap-2 text-sm text-ink-200 hover:text-white">
              <LogIn size={16} /> Sign in
            </NavLink>
          )}
          <div className="hidden md:block mt-3 text-[11px] text-ink-400 font-mono leading-relaxed">
            AI-assisted preliminary risk assessment.
            <br />
            Not a certified structural safety tool.
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
