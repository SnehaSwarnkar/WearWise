import React from 'react'
import './Hero.css'

/* ── Decorative SVG pieces ─────────────────────────────────────── */

const FourPointStar = ({ size = 24, color = '#7953B8', className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={color}
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 0 L13.5 10.5 L24 12 L13.5 13.5 L12 24 L10.5 13.5 L0 12 L10.5 10.5 Z" />
  </svg>
)

const ReviewStars = () => (
  <div className="review-stars">
    {[...Array(5)].map((_, i) => (
      <svg key={i} width="11" height="11" viewBox="0 0 24 24" fill="#7953B8">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    ))}
  </div>
)

const Avatars = () => (
  <div className="avatars">
    {[
      'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=40&h=40&q=80&auto=format&fit=crop&crop=face',
      'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=40&h=40&q=80&auto=format&fit=crop&crop=face',
      'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=40&h=40&q=80&auto=format&fit=crop&crop=face',
    ].map((src, i) => (
      <div key={i} className="avatar" style={{ zIndex: 3 - i }}>
        <img src={src} alt="" />
      </div>
    ))}
  </div>
)

/* ── Curated Unsplash image URLs ───────────────────────────────── */
// Center: tall, elegant, lavender-toned editorial gown
const IMG_CENTER =
  'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=560&q=85&auto=format&fit=crop&crop=top'

// Right: elegant portrait, light/pastel outfit
const IMG_RIGHT =
  'https://images.unsplash.com/photo-1529635696565-cb5c38a661e1?w=380&q=85&auto=format&fit=crop&crop=top'

// Bottom-left: editorial blonde fashion model
const IMG_BOTTOM_LEFT =
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=360&q=85&auto=format&fit=crop&crop=top'

// Collection thumbnail
const IMG_COLLECTION =
  'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=100&q=80&auto=format&fit=crop'

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-canvas">

        {/* ════════════════════════════════════════
            LEFT  COLUMN
            ════════════════════════════════════════ */}
        <div className="hero-left">

          {/* Intro label */}
          <span className="intro-label">Year of 2023</span>

          {/* Main headline */}
          <div className="headline-block">
            <h1 className="heading-secondary">
              discover<br />the secret of
            </h1>

            {/* Decorative tiny star between headings */}
            <FourPointStar size={14} color="#7953B8" className="star-inline" />

            <h1 className="heading-primary">
              Timeless<br />Glamour
            </h1>
          </div>

          {/* Bottom-left oval portrait */}
          <div className="bl-image-wrap">
            <img
              src={IMG_BOTTOM_LEFT}
              alt="Fashion editorial portrait"
              className="img-bl"
            />
          </div>

        </div>

        {/* ════════════════════════════════════════
            CENTER  COLUMN
            ════════════════════════════════════════ */}
        <div className="hero-center">

          {/* Primary hero image */}
          <div className="main-image-wrap">
            <img
              src={IMG_CENTER}
              alt="Elegant lavender gown editorial"
              className="img-main"
            />
            {/* Star decoration upper-right of main image */}
            <FourPointStar size={30} color="#7953B8" className="star-on-main" />
          </div>

          {/* Floating review card – overlapping bottom of main image */}
          <div className="review-card">
            <p className="review-label">Reviews</p>
            <div className="review-row">
              <span className="review-score">4.9</span>
              <div className="review-right">
                <ReviewStars />
                <Avatars />
              </div>
            </div>
          </div>

        </div>

        {/* ════════════════════════════════════════
            RIGHT  COLUMN
            ════════════════════════════════════════ */}
        <div className="hero-right">

          {/* Thin diagonal SVG line behind portrait */}
          <svg className="deco-line" viewBox="0 0 80 260" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="80" y1="0" x2="0" y2="260" stroke="#7953B8" strokeWidth="0.9" strokeDasharray="5 6" opacity="0.35"/>
          </svg>

          {/* Right arched portrait */}
          <div className="right-image-wrap">
            <img
              src={IMG_RIGHT}
              alt="Luxurious ethnic fashion portrait"
              className="img-right"
            />
          </div>

          {/* Body copy */}
          <p className="right-desc">
            Discover a new<br />
            world of fashion<br />
            with a combination of<br />
            beautiful designs and<br />
            quality materials
          </p>

          {/* Collection pill */}
          <div className="collection-pill">
            <div className="pill-thumb">
              <img src={IMG_COLLECTION} alt="Collection preview" />
            </div>
            <div className="pill-text">
              <span className="pill-count">45+</span>
              <span className="pill-label">Collection</span>
            </div>
          </div>

        </div>

        {/* ════════════════════════════════════════
            FLOATING VIEW BUTTON
            ════════════════════════════════════════ */}
        <button className="view-btn" aria-label="View collection">
          View
        </button>

        {/* ════════════════════════════════════════
            BACKGROUND DECORATIVE ELEMENTS
            ════════════════════════════════════════ */}
        <FourPointStar size={10} color="rgba(121,83,184,0.3)"  className="deco-bg deco-bg-1" />
        <FourPointStar size={8}  color="rgba(121,83,184,0.22)" className="deco-bg deco-bg-2" />
        <FourPointStar size={16} color="rgba(121,83,184,0.14)" className="deco-bg deco-bg-3" />
        <FourPointStar size={12} color="rgba(121,83,184,0.18)" className="deco-bg deco-bg-4" />

        {/* Curved connector line behind images */}
        <svg className="deco-arc" viewBox="0 0 320 60" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M 0 50 Q 160 -10 320 30" stroke="#7953B8" strokeWidth="0.7"
                strokeDasharray="6 7" opacity="0.25" fill="none"/>
        </svg>

      </div>
    </section>
  )
}
