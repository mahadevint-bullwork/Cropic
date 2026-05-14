import { useState, useEffect } from "react";
import "./App.css";

function App() {

  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);

  const [prediction, setPrediction] = useState("");

  const [details, setDetails] = useState({
    cause: "",
    severity: "",
    stage: "",
    crop_type: ""
  });

  const [historyImages, setHistoryImages] = useState([]);

  const [loading, setLoading] = useState(false);

  const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000";

  // ======================
  // FETCH HISTORY
  // ======================

  const fetchImages = async () => {

    try {

      const res = await fetch(`${BASE_URL}/images`);
      const data = await res.json();

      setHistoryImages(data.images);

    } catch (err) {

      console.log(err);

    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  // ======================
  // IMAGE SELECT
  // ======================

  const handleImage = (e) => {

    const file = e.target.files[0];

    if (!file) return;

    setImage(file);

    setPreview(URL.createObjectURL(file));

    setPrediction("");

    setDetails({
      cause: "",
      severity: "",
      stage: "",
      crop_type: ""
    });
  };

  // ======================
  // UPLOAD + PREDICT
  // ======================

  const uploadAndPredict = async () => {

    if (!image) {
      alert("Select image first");
      return;
    }

    setLoading(true);

    const formData = new FormData();

    formData.append("image", image);

    try {

      // Upload

      const uploadRes = await fetch(`${BASE_URL}/upload`, {
        method: "POST",
        body: formData
      });

      const uploadData = await uploadRes.json();

      const filename = uploadData.filename;

      // Predict

      const predictRes = await fetch(
        `${BASE_URL}/predict/${filename}`,
        {
          method: "POST"
        }
      );

      const predictData = await predictRes.json();

      setPrediction(predictData.condition);

      setDetails({
        cause: predictData.cause,
        severity: predictData.severity,
        stage: predictData.stage,
        crop_type: predictData.crop_type
      });

      fetchImages();

    } catch (err) {

      console.log(err);
      alert("Error occurred");

    }

    setLoading(false);
  };

  return (

    <div className="container">

      {/* HEADER */}

      <div className="header">

        <div>
          <h1>🌿 Crop Health Analyzer</h1>

          <p className="subtitle">
            AI Powered Crop Disease Detection System
          </p>
        </div>

      </div>

      {/* MAIN SECTION */}

      <div className="main-section">

        {/* LEFT */}

        <div className="left-panel">

          <div className="image-card">

            {preview ? (

              <img
                src={preview}
                alt="preview"
                className="preview-image"
              />

            ) : (

              <div className="placeholder">

                <h3>Upload Crop Image</h3>

                <p>
                  JPG, PNG, JPEG
                </p>

              </div>

            )}

          </div>

        </div>

        {/* RIGHT */}

        <div className="right-panel">

          <h2>Analyze Crop Health</h2>

          <p className="small-text">
            Upload a crop image to detect diseases,
            severity and growth stage.
          </p>

          <div className="upload-box">

            <input
              type="file"
              accept="image/*"
              onChange={handleImage}
            />

          </div>

          <button onClick={uploadAndPredict}>
            🔍 Analyze Image
          </button>

          {loading && (
            <p className="loading-text">
              Analyzing image...
            </p>
          )}

        </div>

      </div>

      {/* RESULT */}

      {prediction && !loading && (

        <div className="result-card">

          <h2>Prediction Result</h2>

          <div className="result-grid">

            <div className="result-item">
              <span>Crop Type</span>
              <strong>{details.crop_type}</strong>
            </div>

            <div className="result-item">
              <span>Condition</span>
              <strong>{prediction}</strong>
            </div>

            <div className="result-item">
              <span>Cause</span>
              <strong>{details.cause}</strong>
            </div>

            <div className="result-item">
              <span>Severity</span>
              <strong>{details.severity}</strong>
            </div>

            <div className="result-item">
              <span>Stage</span>
              <strong>{details.stage}</strong>
            </div>

          </div>

        </div>
      )}

      {/* HISTORY */}

      <div className="history-section">

        <h2>🕘 Recent Analyses</h2>

        <div className="history-container">

          {historyImages.map((img, index) => (

            <img
              key={index}
              src={`${BASE_URL}/uploads/${img}`}
              alt="history"
              className="history-image"
            />

          ))}

        </div>

      </div>

    </div>
  );
}

export default App;