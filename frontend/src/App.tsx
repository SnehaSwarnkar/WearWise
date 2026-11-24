import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

// ── Storefront Pages ─────────────────────────────────────────────────────────
import Home from './pages/Home';
import Explore from './pages/Explore';
import MyStyle from './pages/MyStyle';
import TryOn from './pages/TryOn';
import StyleAnalysis from './pages/StyleAnalysis';
import ChooseLook from './pages/ChooseLook';
import BuildAvatar from './pages/BuildAvatar';
import Wardrobe from './pages/Wardrobe';
import FashionAssistant from './pages/FashionAssistant';
import SavedLooks from './pages/SavedLooks';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import OrderConfirmation from './pages/OrderConfirmation';
import Login from './pages/Login';
import Signup from './pages/Signup';
import GenderSelect from './pages/GenderSelect';
import MenSetup from './pages/MenSetup';
import WomenSetup from './pages/WomenSetup';
import KidsSetup from './pages/KidsSetup';
import MenShop from './pages/MenShop';
import WomenShop from './pages/WomenShop';
import KidsShop from './pages/KidsShop';
import MyOrders from './pages/MyOrders';

// ── Body Engine & Honest Fit Pages ──────────────────────────────────────────
import { Dashboard } from './pages/Dashboard';
import { BodyProfilePage } from './pages/BodyProfile';
import { AvatarStudio } from './pages/AvatarStudio';
import { GarmentStudio } from './pages/GarmentStudio';
import { HonestFitPage } from './pages/HonestFit';
import MerchantGarmentStudio from './pages/MerchantGarmentStudio';

/** Redirect unauthenticated commerce shoppers to /login */
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

export const App: React.FC = () => {
  return (
    <Routes>
      {/* ── Public Storefront ── */}
      <Route path="/" element={<Home />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/my-style" element={<MyStyle />} />
      <Route path="/try-on" element={<TryOn />} />
      <Route path="/style-analysis" element={<StyleAnalysis />} />
      <Route path="/choose-look" element={<ChooseLook />} />
      <Route path="/build-avatar" element={<BuildAvatar />} />
      <Route path="/wardrobe" element={<Wardrobe />} />
      <Route path="/saved" element={<SavedLooks />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/order-confirmation" element={<OrderConfirmation />} />
      <Route path="/fashion-assistant" element={<FashionAssistant />} />

      {/* ── Commerce Auth ── */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* ── Onboarding (requires user auth) ── */}
      <Route path="/select-gender" element={<PrivateRoute><GenderSelect /></PrivateRoute>} />
      <Route path="/men-setup" element={<PrivateRoute><MenSetup /></PrivateRoute>} />
      <Route path="/women-setup" element={<PrivateRoute><WomenSetup /></PrivateRoute>} />
      <Route path="/kids-setup" element={<PrivateRoute><KidsSetup /></PrivateRoute>} />

      {/* ── Gender Shops (requires user auth) ── */}
      <Route path="/men-shop" element={<PrivateRoute><MenShop /></PrivateRoute>} />
      <Route path="/women-shop" element={<PrivateRoute><WomenShop /></PrivateRoute>} />
      <Route path="/kids-shop" element={<PrivateRoute><KidsShop /></PrivateRoute>} />

      {/* ── Customer Orders ── */}
      <Route path="/orders" element={<PrivateRoute><MyOrders /></PrivateRoute>} />
      <Route path="/orders/:id" element={<PrivateRoute><MyOrders /></PrivateRoute>} />

      {/* ── Body Engine & Honest Fit (Preserved, Executive Dashboard at /my-fit) ── */}
      <Route path="/my-fit" element={<Dashboard />} />
      <Route path="/profile" element={<BodyProfilePage />} />
      <Route path="/avatar" element={<AvatarStudio />} />
      <Route path="/fit" element={<HonestFitPage />} />
      <Route path="/garments" element={<GarmentStudio />} />
      <Route path="/merchant/garment-studio" element={<MerchantGarmentStudio />} />
      <Route path="/merchant-studio" element={<MerchantGarmentStudio />} />

      {/* ── Catch-all redirects to Home ── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
