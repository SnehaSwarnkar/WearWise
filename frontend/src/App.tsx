import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import PortalAccessDenied from './components/PortalAccessDenied';

// ── Storefront & Auth Pages ──────────────────────────────────────────────────
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
import AuthLandingPage from './pages/AuthLandingPage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import SellerLoginPage from './pages/SellerLoginPage';
import SellerRegisterInfoPage from './pages/SellerRegisterInfoPage';
import GenderSelect from './pages/GenderSelect';
import MenSetup from './pages/MenSetup';
import WomenSetup from './pages/WomenSetup';
import KidsSetup from './pages/KidsSetup';
import MenShop from './pages/MenShop';
import WomenShop from './pages/WomenShop';
import KidsShop from './pages/KidsShop';
import MyOrders from './pages/MyOrders';

// ── Seller Portal Pages ──────────────────────────────────────────────────────
import SellerDashboardPage from './pages/seller/SellerDashboardPage';
import SellerProductsPage from './pages/seller/SellerProductsPage';
import SellerOrdersPage from './pages/seller/SellerOrdersPage';
import SellerStudioPage from './pages/seller/SellerStudioPage';
import SellerProfilePage from './pages/seller/SellerProfilePage';

// ── Body Engine & Honest Fit Pages ──────────────────────────────────────────
import { Dashboard } from './pages/Dashboard';
import { BodyProfilePage } from './pages/BodyProfile';
import { AvatarStudio } from './pages/AvatarStudio';
import { HonestFitPage } from './pages/HonestFit';
import Phase10SimPage from './experimental_phase10/Phase10SimPage';
import ExperimentalTryOnPage from './experimental_phase10/ExperimentalTryOnPage';
import ProductDetailPage from './pages/ProductDetailPage';
import ImageTryOnPage from './pages/ImageTryOnPage';

/** Shopper-protected route guard: requires authenticated `shopper` account. */
function ShopperRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, isShopper, isSeller } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (isSeller || !isShopper) {
    return (
      <PortalAccessDenied
        requiredPortal="Shopper Portal"
        message="This area is reserved for WearWise shoppers. Please return to the Seller Portal or sign in with a shopper account."
        returnTo="/seller/dashboard"
        returnLabel="Go to Seller Dashboard →"
      />
    );
  }
  return <>{children}</>;
}

/** Seller-protected route guard: requires authenticated, active, approved `seller` account. */
function SellerRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, isSeller } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/seller/login" replace />;
  if (!isSeller) {
    return (
      <PortalAccessDenied
        requiredPortal="Seller Portal"
        message="Seller privileges are required to access Seller Dashboard, Inventory, and Studio controls."
        returnTo="/explore"
        returnLabel="Return to Shopper Marketplace →"
      />
    );
  }
  return <>{children}</>;
}

export const App: React.FC = () => {
  return (
    <Routes>
      {/* ── Public Storefront & Try-On ── */}
      <Route path="/" element={<Home />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/product/:sku" element={<ProductDetailPage />} />
      <Route path="/image-try-on" element={<ImageTryOnPage />} />
      <Route path="/try-on" element={<TryOn />} />
      <Route path="/experimental-phase10" element={<Phase10SimPage />} />
      <Route path="/experimental-try-on" element={<ExperimentalTryOnPage />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/order-confirmation" element={<OrderConfirmation />} />

      {/* ── Dual-Portal Authentication Entry ── */}
      <Route path="/auth" element={<AuthLandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Signup />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/seller/login" element={<SellerLoginPage />} />
      <Route path="/seller/register" element={<SellerRegisterInfoPage />} />

      {/* ── Shopper-Protected Portal ── */}
      <Route path="/my-style" element={<ShopperRoute><MyStyle /></ShopperRoute>} />
      <Route path="/style-analysis" element={<ShopperRoute><StyleAnalysis /></ShopperRoute>} />
      <Route path="/choose-look" element={<ShopperRoute><ChooseLook /></ShopperRoute>} />
      <Route path="/build-avatar" element={<ShopperRoute><BuildAvatar /></ShopperRoute>} />
      <Route path="/wardrobe" element={<ShopperRoute><Wardrobe /></ShopperRoute>} />
      <Route path="/saved" element={<ShopperRoute><SavedLooks /></ShopperRoute>} />
      <Route path="/fashion-assistant" element={<ShopperRoute><FashionAssistant /></ShopperRoute>} />

      <Route path="/select-gender" element={<ShopperRoute><GenderSelect /></ShopperRoute>} />
      <Route path="/men-setup" element={<ShopperRoute><MenSetup /></ShopperRoute>} />
      <Route path="/women-setup" element={<ShopperRoute><WomenSetup /></ShopperRoute>} />
      <Route path="/kids-setup" element={<ShopperRoute><KidsSetup /></ShopperRoute>} />

      <Route path="/men-shop" element={<ShopperRoute><MenShop /></ShopperRoute>} />
      <Route path="/women-shop" element={<ShopperRoute><WomenShop /></ShopperRoute>} />
      <Route path="/kids-shop" element={<ShopperRoute><KidsShop /></ShopperRoute>} />

      <Route path="/orders" element={<ShopperRoute><MyOrders /></ShopperRoute>} />
      <Route path="/orders/:id" element={<ShopperRoute><MyOrders /></ShopperRoute>} />

      <Route path="/my-fit" element={<ShopperRoute><Dashboard /></ShopperRoute>} />
      <Route path="/profile" element={<ShopperRoute><BodyProfilePage /></ShopperRoute>} />
      <Route path="/avatar" element={<ShopperRoute><AvatarStudio /></ShopperRoute>} />
      <Route path="/fit" element={<ShopperRoute><HonestFitPage /></ShopperRoute>} />

      {/* ── Seller-Protected Portal ── */}
      <Route path="/seller" element={<Navigate to="/seller/dashboard" replace />} />
      <Route path="/seller/dashboard" element={<SellerRoute><SellerDashboardPage /></SellerRoute>} />
      <Route path="/seller/products" element={<SellerRoute><SellerProductsPage /></SellerRoute>} />
      <Route path="/seller/products/new" element={<SellerRoute><SellerProductsPage openCreateDefault /></SellerRoute>} />
      <Route path="/seller/inventory" element={<SellerRoute><SellerProductsPage inventoryMode /></SellerRoute>} />
      <Route path="/seller/studio" element={<SellerRoute><SellerStudioPage /></SellerRoute>} />
      <Route path="/seller/orders" element={<SellerRoute><SellerOrdersPage /></SellerRoute>} />
      <Route path="/seller/profile" element={<SellerRoute><SellerProfilePage /></SellerRoute>} />
      <Route path="/seller/settings" element={<SellerRoute><SellerProfilePage settingsMode /></SellerRoute>} />

      {/* ── Legacy Merchant Studio Aliases (Strictly Seller-Guarded) ── */}
      <Route path="/merchant/garment-studio" element={<SellerRoute><Navigate to="/seller/studio" replace /></SellerRoute>} />
      <Route path="/merchant-studio" element={<SellerRoute><Navigate to="/seller/studio" replace /></SellerRoute>} />
      <Route path="/garments" element={<SellerRoute><Navigate to="/seller/products" replace /></SellerRoute>} />

      {/* ── Catch-all redirects to Home ── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
