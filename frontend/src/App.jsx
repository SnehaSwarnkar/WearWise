import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

// ── Timeless Glamour home (unchanged) ──
import TimelessHome from './pages/TimelessHome'

// ── WearWise pages ──
import Login           from './pages/Login'
import Signup          from './pages/Signup'
import GenderSelect    from './pages/GenderSelect'
import MenSetup        from './pages/MenSetup'
import WomenSetup      from './pages/WomenSetup'
import KidsSetup       from './pages/KidsSetup'
import MenShop         from './pages/MenShop'
import WomenShop       from './pages/WomenShop'
import KidsShop        from './pages/KidsShop'
import Explore         from './pages/Explore'
import MyStyle         from './pages/MyStyle'
import TryOn           from './pages/TryOn'
import ChooseLook      from './pages/ChooseLook'
import StyleAnalysis   from './pages/StyleAnalysis'
import BuildAvatar     from './pages/BuildAvatar'
import FashionAssistant from './pages/FashionAssistant'
import Wardrobe        from './pages/Wardrobe'
import SavedLooks      from './pages/SavedLooks'
import Cart            from './pages/Cart'
import Checkout        from './pages/Checkout'
import OrderConfirmation from './pages/OrderConfirmation'
import MyOrders        from './pages/MyOrders'

import './App.css'

/** Guard: redirect unauthenticated users to /login */
function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      {/* ── Timeless Glamour homepage (unchanged) ── */}
      <Route path="/" element={<TimelessHome />} />

      {/* ── Auth ── */}
      <Route path="/login"  element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* ── Onboarding (requires auth) ── */}
      <Route path="/select-gender" element={<PrivateRoute><GenderSelect /></PrivateRoute>} />
      <Route path="/men-setup"     element={<PrivateRoute><MenSetup /></PrivateRoute>} />
      <Route path="/women-setup"   element={<PrivateRoute><WomenSetup /></PrivateRoute>} />
      <Route path="/kids-setup"    element={<PrivateRoute><KidsSetup /></PrivateRoute>} />

      {/* ── Gender shops ── */}
      <Route path="/men-shop"   element={<PrivateRoute><MenShop /></PrivateRoute>} />
      <Route path="/women-shop" element={<PrivateRoute><WomenShop /></PrivateRoute>} />
      <Route path="/kids-shop"  element={<PrivateRoute><KidsShop /></PrivateRoute>} />

      {/* ── Open WearWise pages ── */}
      <Route path="/explore"            element={<Explore />} />
      <Route path="/my-style"           element={<MyStyle />} />
      <Route path="/try-on"             element={<TryOn />} />
      <Route path="/choose-look"        element={<ChooseLook />} />
      <Route path="/style-analysis"     element={<StyleAnalysis />} />
      <Route path="/build-avatar"       element={<BuildAvatar />} />
      <Route path="/fashion-assistant"  element={<FashionAssistant />} />
      <Route path="/wardrobe"           element={<Wardrobe />} />
      <Route path="/saved"              element={<SavedLooks />} />
      <Route path="/cart"               element={<Cart />} />
      <Route path="/checkout"           element={<Checkout />} />
      <Route path="/order-confirmation" element={<OrderConfirmation />} />

      {/* ── Orders (authenticated) ── */}
      <Route path="/orders"     element={<PrivateRoute><MyOrders /></PrivateRoute>} />
      <Route path="/orders/:id" element={<PrivateRoute><MyOrders /></PrivateRoute>} />
    </Routes>
  )
}

export default App
