import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

// Existing pages
import Home            from "./pages/Home";
import Explore         from "./pages/Explore";
import MyStyle         from "./pages/MyStyle";
import TryOn           from "./pages/TryOn";
import StyleAnalysis   from "./pages/StyleAnalysis";
import ChooseLook      from "./pages/ChooseLook";
import BuildAvatar     from "./pages/BuildAvatar";
import Wardrobe        from "./pages/Wardrobe";
import FashionAssistant from "./pages/FashionAssistant";
import SavedLooks      from "./pages/SavedLooks";
import Cart            from "./pages/Cart";
import Checkout        from "./pages/Checkout";
import OrderConfirmation from "./pages/OrderConfirmation";

// New onboarding + shop pages
import Login           from "./pages/Login";
import Signup          from "./pages/Signup";
import GenderSelect    from "./pages/GenderSelect";
import MenSetup        from "./pages/MenSetup";
import WomenSetup      from "./pages/WomenSetup";
import KidsSetup       from "./pages/KidsSetup";
import MenShop         from "./pages/MenShop";
import WomenShop       from "./pages/WomenShop";
import KidsShop        from "./pages/KidsShop";

/** Redirect unauthenticated users to /login */
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Routes>
      {/* ── Public ── */}
      <Route path="/login"  element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* ── Onboarding (requires auth) ── */}
      <Route path="/select-gender" element={<PrivateRoute><GenderSelect /></PrivateRoute>} />
      <Route path="/men-setup"     element={<PrivateRoute><MenSetup /></PrivateRoute>} />
      <Route path="/women-setup"   element={<PrivateRoute><WomenSetup /></PrivateRoute>} />
      <Route path="/kids-setup"    element={<PrivateRoute><KidsSetup /></PrivateRoute>} />

      {/* ── Gender shops (requires auth) ── */}
      <Route path="/men-shop"   element={<PrivateRoute><MenShop /></PrivateRoute>} />
      <Route path="/women-shop" element={<PrivateRoute><WomenShop /></PrivateRoute>} />
      <Route path="/kids-shop"  element={<PrivateRoute><KidsShop /></PrivateRoute>} />

      {/* ── Existing pages (public) ── */}
      <Route path="/"                   element={<Home />} />
      <Route path="/explore"            element={<Explore />} />
      <Route path="/my-style"           element={<MyStyle />} />
      <Route path="/try-on"             element={<TryOn />} />
      <Route path="/style-analysis"     element={<StyleAnalysis />} />
      <Route path="/choose-look"        element={<ChooseLook />} />
      <Route path="/build-avatar"       element={<BuildAvatar />} />
      <Route path="/wardrobe"           element={<Wardrobe />} />
      <Route path="/saved"              element={<SavedLooks />} />
      <Route path="/cart"               element={<Cart />} />
      <Route path="/checkout"           element={<Checkout />} />
      <Route path="/order-confirmation" element={<OrderConfirmation />} />
      <Route path="/fashion-assistant"  element={<FashionAssistant />} />
    </Routes>
  );
}

export default App;
