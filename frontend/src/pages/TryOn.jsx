import { useState } from "react";
import "../App.css";
import { Link, useNavigate } from "react-router-dom";
import Header from "./Header";

function TryOn() {
  const [selectedImage, setSelectedImage] = useState(null);
  const navigate = useNavigate();

  const handleImageChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    setSelectedImage(imageUrl);
  };

  const removePhoto = () => {
    setSelectedImage(null);
  };

  return (
    <div className="tryon-page">
      <Header />
      
      <main className="tryon-editorial">

        {/* TOP LABEL */}
        <div className="tryon-editorial-top">
          <span>✦ AI VIRTUAL TRY ON</span>
          <span>STEP 01 / 03</span>
        </div>

        {/* HERO */}
        <section className="tryon-hero">

          {/* LEFT EDITORIAL TEXT */}
          <div className="tryon-editorial-copy">
            <div className="tryon-side-label">
              YOUR DIGITAL
              <br />
              FITTING ROOM
            </div>

            <h1>
              DROP
              <br />
              <span>YOUR</span>
              <br />
              PHOTO.
            </h1>

            <p>
              Start with a clear photo of yourself.
              AI Fashion will use it as the canvas for
              your next look.
            </p>
          </div>

          {/* MAIN PHOTO DROP AREA */}
          <div className="photo-drop-stage">

            <div className="stage-purple-shape"></div>
            <div className="stage-orange-shape"></div>
            <div className="stage-yellow-dot"></div>

            <div className="photo-drop-card">

              <div className="photo-card-top">
                <span>
                  ✦ {selectedImage ? "PHOTO READY" : "PHOTO INPUT"}
                </span>

                <span>01 / 03</span>
              </div>

              <div className="photo-drop-center">

                {!selectedImage ? (
                  <>
                    <div className="photo-placeholder">
                      <div className="photo-head"></div>
                      <div className="photo-body"></div>
                    </div>

                    <div className="drop-copy">
                      <span>DRAG & DROP</span>

                      <h2>
                        YOUR
                        <br />
                        PHOTO
                      </h2>

                      <p>
                        A clear full-body photo
                        <br />
                        works best.
                      </p>

                      <label className="editorial-upload-btn">
                        CHOOSE PHOTO

                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageChange}
                        />
                      </label>
                    </div>
                  </>
                ) : (
                  <div className="uploaded-editorial-view">

                    <img
                      src={selectedImage}
                      alt="Selected fashion photo"
                      className="uploaded-editorial-image"
                    />

                    <div className="uploaded-editorial-overlay">
                      <div>
                        <span>✦ PHOTO LOADED</span>
                        <h3>READY FOR YOUR LOOK</h3>
                      </div>

                      <div className="photo-actions">

                        <label className="change-photo-btn">
                          CHANGE PHOTO

                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleImageChange}
                          />
                        </label>

                        <button
                          type="button"
                          className="remove-photo-btn"
                          onClick={removePhoto}
                        >
                          REMOVE PHOTO
                        </button>

                      </div>
                    </div>

                  </div>
                )}

              </div>

              <div className="photo-card-bottom">

                <span>
                  {selectedImage
                    ? "PHOTO READY FOR AI"
                    : "FRONT VIEW PREFERRED"}
                </span>

                {selectedImage ? (
                  <button
                    type="button"
                    className="continue-to-look-btn"
                    onClick={() => navigate("/choose-look")}
                  >
                    CONTINUE TO STEP 2 →
                  </button>
                ) : (
                  <span>JPG / PNG</span>
                )}

              </div>

            </div>

          </div>

          {/* RIGHT EDITORIAL INFO */}
          <div className="tryon-right-details">

            <div className="right-detail-number">
              2026
            </div>

            <div className="right-detail-text">
              YOUR LOOK
              <br />
              STARTS
              <br />
              HERE
            </div>

            <div className="tryon-star">
              ✦
            </div>

          </div>

        </section>

        {/* BOTTOM SECTION */}
        <section className="tryon-bottom">

          <div className="tryon-privacy">
            <span>✦</span>
            PRIVATE PHOTO PROCESSING
          </div>

          <div className="tryon-flow">

            <div
              className={`flow-item ${
                selectedImage ? "complete" : "active"
              }`}
            >
              <span>01</span>

              <div>
                <strong>UPLOAD</strong>

                <small>
                  {selectedImage ? "Photo ready" : "Your photo"}
                </small>
              </div>
            </div>

            <div className="flow-line"></div>

            <div
              className={`flow-item ${
                selectedImage ? "active" : ""
              }`}
            >
              <span>02</span>

              <div>
                <strong>CHOOSE</strong>
                <small>Your outfit</small>
              </div>
            </div>

            <div className="flow-line"></div>

            <div className="flow-item">
              <span>03</span>

              <div>
                <strong>TRY ON</strong>
                <small>Your AI look</small>
              </div>
            </div>

          </div>

          <div className="tryon-bottom-tag">
            AI FASHION
            <span>✦</span>
          </div>

        </section>

      </main>

    </div>
  );
}

export default TryOn;