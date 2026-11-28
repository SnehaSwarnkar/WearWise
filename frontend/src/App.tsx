import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import PortalAccessDenied from './components/PortalAccessDenied';

// ── Customer & Public Storefront Pages ───────────────────────────────────────
import Home from './pages/Home';
import Explore from './pages/Explore';
import ShopPage from './pages/ShopPage';
import MenShop from './pages/MenShop';
import WomenShop from './pages/WomenShop';
import KidsShop from './pages/KidsShop';
import ProductDetailPage from './pages/ProductDetailPage';
import ImageTryOnPage from './pages/ImageTryOnPage';
import ExperimentalTryOnPage from './experimental_phase10/ExperimentalTryOnPage';
import AvatarLandingPage from './pages/avatar/AvatarLandingPage';
import AvatarCreateWizard from './pages/avatar/AvatarCreateWizard';
import AvatarDashboardPage from './pages/avatar/AvatarDashboardPage';
import SavedLooks from './pages/SavedLooks';
import MyOrders from './pages/MyOrders';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import OrderConfirmation from './pages/OrderConfirmation';
import ProfilePage from './pages/ProfilePage';

// ── Authentication Entry Pages ───────────────────────────────────────────────
import AuthLandingPage from './pages/AuthLandingPage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import SellerLoginPage from './pages/SellerLoginPage';
import SellerRegisterInfoPage from './pages/SellerRegisterInfoPage';

// ── Seller Portal Pages ──────────────────────────────────────────────────────
import SellerDashboardPage from './pages/seller/SellerDashboardPage';
import SellerProductsPage from './pages/seller/SellerProductsPage';
import SellerOrdersPage from './pages/seller/SellerOrdersPage';
import SellerStudioPage from './pages/seller/SellerStudioPage';
import SellerProfilePage from './pages/seller/SellerProfilePage';

// ── Admin Portal & Internal Diagnostics (Admin-Guarded) ──────────────────────
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import Phase10SimPage from './experimental_phase10/Phase10SimPage';

// ── Isolated Auxiliary Shopper Pages (non-navbar) ────────────────────────────
import Wardrobe from './pages/Wardrobe';
import { HonestFitPage } from './pages/HonestFit';

/** Customer-protected route guard: requires authenticated `shopper` account. */
function ShopperRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, isShopper, isSeller, isAdmin } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (isAdmin) {
    return (
      <PortalAccessDenied
        requiredPortal="Shopper Portal"
        message="This area is reserved for WearWise customers. Return to the Admin Console or sign in with a customer account."
        returnTo="/admin"
        returnLabel="Go to Admin Console →"
      />
    );
  }
  if (isSeller || !isShopper) {
    return (
      <PortalAccessDenied
        requiredPortal="Shopper Portal"
        message="This area is reserved for WearWise customers. Please return to the Seller Portal or sign in with a customer account."
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
        returnLabel="Return to Marketplace →"
      />
    );
  }
  return <>{children}</>;
}

/** Admin-protected route guard: requires authenticated `admin` account. */
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, isAdmin } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/admin/login" replace />;
  if (!isAdmin) {
    return (
      <PortalAccessDenied
        requiredPortal="Admin Portal"
        message="Administrator privileges are required to access WearWise Platform Management."
        returnTo="/home"
        returnLabel="Return to Storefront →"
      />
    );
  }
  return <>{children}</>;
}

export const App: React.FC = () => {
  return (
    <Routes>
      {/* ── Customer Storefront Routes ── */}
      <Route path="/" element={<Home />} />
      <Route path="/home" element={<Home />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/shop" element={<ShopPage sectionGender="all" />} />
      <Route path="/shop/men" element={<MenShop />} />
      <Route path="/shop/women" element={<WomenShop />} />
      <Route path="/shop/kids" element={<KidsShop />} />
      <Route path="/product/:sku" element={<ProductDetailPage />} />
      <Route path="/image-try-on" element={<ImageTryOnPage />} />
      <Route path="/try-on" element={<ExperimentalTryOnPage />} />
      <Route path="/experimental-try-on" element={<ExperimentalTryOnPage />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/order-confirmation" element={<OrderConfirmation />} />

      {/* ── Role-Separated Authentication Entry ── */}
      <Route path="/auth" element={<AuthLandingPage />} />
      <Route path="/login" element={<Login initialRole="customer" />} />
      <Route path="/admin/login" element={<Login initialRole="admin" />} />
      <Route path="/register" element={<Signup />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/seller/login" element={<SellerLoginPage />} />
      <Route path="/seller/register" element={<SellerRegisterInfoPage />} />

      {/* ── Customer Protected Destinations ── */}
      <Route path="/avatar" element={<ShopperRoute><AvatarLandingPage /></ShopperRoute>} />
      <Route path="/avatar/create" element={<ShopperRoute><AvatarCreateWizard /></ShopperRoute>} />
      <Route path="/avatar/dashboard" element={<ShopperRoute><AvatarDashboardPage /></ShopperRoute>} />
      <Route path="/wishlist" element={<ShopperRoute><SavedLooks /></ShopperRoute>} />
      <Route path="/saved" element={<ShopperRoute><SavedLooks /></ShopperRoute>} />
      <Route path="/orders" element={<ShopperRoute><MyOrders /></ShopperRoute>} />
      <Route path="/orders/:id" element={<ShopperRoute><MyOrders /></ShopperRoute>} />
      <Route path="/profile" element={<ShopperRoute><ProfilePage /></ShopperRoute>} />

      {/* ── Legacy Customer Route Redirects / Compatibility ── */}
      <Route path="/men-shop" element={<Navigate to="/shop/men" replace />} />
      <Route path="/women-shop" element={<Navigate to="/shop/women" replace />} />
      <Route path="/kids-shop" element={<Navigate to="/shop/kids" replace />} />
      <Route path="/wardrobe" element={<ShopperRoute><Wardrobe /></ShopperRoute>} />
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

      {/* ── Admin-Protected Portal & Diagnostics ── */}
      <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
      <Route path="/admin/diagnostics" element={<AdminRoute><Phase10SimPage /></AdminRoute>} />
      <Route path="/experimental-phase10" element={<AdminRoute><Phase10SimPage /></AdminRoute>} />

      {/* ── Catch-all redirects to Home ── */}
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
};

export default App;
