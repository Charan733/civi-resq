import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Shell from "./components/Shell";
import Dashboard from "./pages/Dashboard";
import RiskMap from "./pages/RiskMap";
import ZoneDetail from "./pages/ZoneDetail";
import Simulator from "./pages/Simulator";
import Assistant from "./pages/Assistant";
import Login from "./pages/Login";
import UploadData from "./pages/UploadData";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="*"
            element={
              <Shell>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/map" element={<RiskMap />} />
                  <Route path="/zones/:id" element={<ZoneDetail />} />
                  <Route path="/simulator" element={<Simulator />} />
                  <Route path="/assistant" element={<Assistant />} />
                  <Route path="/upload" element={<UploadData />} />
                </Routes>
              </Shell>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
