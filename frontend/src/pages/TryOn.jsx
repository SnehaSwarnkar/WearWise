import { useState } from "react";
import "../App.css";
import { Link } from "react-router-dom";

function TryOn() {
  const [selectedImage, setSelectedImage] = useState(null);

  const handleImageChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setSelectedImage(imageUrl);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
  };

  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="logo">
          AI <span>FASHION</span>
        </Link>

        <div className="nav-links">
          <Link to="/explore">Explore</Link>
          <Link to="/my-style">My Style</Link>
          <Link to="/try-on">Try On</Link>
        </div>

        <Link to="/my-style" className="profile-btn">
          My Profile
        </Link>
      </nav>

      <main className="placeholder-page">
        <p className="hero-tag">VIRTUAL TRY-ON</p>

        <h1>
          See it on
          <br />
          <span>you first.</span>
        </h1>

        <p>
          Upload a clear, front-facing photo and prepare to visualize
          different outfits on yourself.
        </p>

        {!selectedImage ? (
          <div className="tryon-upload-box">
            <div className="upload-icon">🪞</div>

            <h2>Upload Your Photo</h2>

            <p>
              Choose a clear, front-facing image for the best virtual try-on
              experience.
            </p>

            <label htmlFor="image-upload" className="primary-btn upload-btn">
              Upload Image
            </label>

            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              hidden
            />

            <small>
              Your image will only be used for your AI Fashion experience.
            </small>
          </div>
        ) : (
          <div className="image-preview-box">
            <h2>Your Photo</h2>

            <img
              src={selectedImage}
              alt="Selected for virtual try-on"
              className="image-preview"
            />

            <div className="preview-buttons">
              <label
                htmlFor="image-upload"
                className="secondary-btn upload-btn"
              >
                Change Photo
              </label>

              <input
                id="image-upload"
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                hidden
              />

              <button className="remove-btn" onClick={removeImage}>
                Remove
              </button>
            </div>

            <button className="primary-btn continue-btn">
              Continue to Try-On →
            </button>
          </div>
        )}

        <Link to="/explore" className="secondary-btn">
          🛍 Explore Clothes First
        </Link>
      </main>
    </div>
  );
}

export default TryOn;