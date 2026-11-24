import React, { useState } from 'react'
import { Search, ShoppingBag, User, Menu, X } from 'lucide-react'
import './Navbar.css'

const BrandLogo = () => (
  <div className="brand-logo">
    <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" className="brand-logo-svg">
      <circle cx="18" cy="18" r="18" fill="#7953B8"/>
      <polygon points="18,8 23,20 13,20" fill="white" opacity="0.95"/>
      <line x1="18" y1="20" x2="18" y2="28" stroke="white" strokeWidth="1.5" opacity="0.7"/>
      <line x1="13" y1="24" x2="23" y2="24" stroke="white" strokeWidth="1.2" opacity="0.5"/>
    </svg>
  </div>
)

const navLinks = ['Home', 'Collections', 'Sale', 'Stories', 'Contact Us']

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Logo + Brand name */}
        <div className="navbar-brand">
          <BrandLogo />
          <span className="brand-name">Timeless</span>
        </div>

        {/* Desktop nav links */}
        <ul className="nav-links">
          {navLinks.map((link, i) => (
            <li key={link}>
              <a href="#" className={`nav-link${i === 0 ? ' active' : ''}`}>{link}</a>
            </li>
          ))}
        </ul>

        {/* Icons */}
        <div className="nav-icons">
          <button className="nav-icon-btn" aria-label="Search">
            <Search size={18} strokeWidth={1.5} />
          </button>
          <button className="nav-icon-btn" aria-label="Shopping bag">
            <ShoppingBag size={18} strokeWidth={1.5} />
          </button>
          <button className="nav-icon-btn" aria-label="Profile">
            <User size={18} strokeWidth={1.5} />
          </button>
        </div>

        {/* Mobile hamburger */}
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Menu">
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="mobile-menu">
          {navLinks.map(link => (
            <a key={link} href="#" className="mobile-link" onClick={() => setMenuOpen(false)}>{link}</a>
          ))}
          <div className="mobile-icons">
            <Search size={18} strokeWidth={1.5} />
            <ShoppingBag size={18} strokeWidth={1.5} />
            <User size={18} strokeWidth={1.5} />
          </div>
        </div>
      )}
    </nav>
  )
}
