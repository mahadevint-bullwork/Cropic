const express = require("express");
const multer = require("multer");
const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const cors = require("cors");

const app = express();

// ======================
// CORS - allow app to connect
// ======================
app.use(cors());

// ======================
// LOGGER
// ======================
const logDir = path.join(__dirname, "logs");
if (!fs.existsSync(logDir)) fs.mkdirSync(logDir);

const logFile = path.join(logDir, "server.log");

function logToFile(message) {
  const time = new Date().toISOString();
  const log = `[${time}] ${message}\n`;
  fs.appendFile(logFile, log, (err) => {
    if (err) console.error("Log write error:", err);
  });
}

app.use((req, res, next) => {
  const start = Date.now();
  logToFile(`REQ ${req.method} ${req.url}`);
  res.on("finish", () => {
    const duration = Date.now() - start;
    logToFile(`RES ${req.method} ${req.url} ${res.statusCode} ${duration}ms`);
  });
  next();
});

// ======================
// STATIC
// ======================
app.use(express.static(path.join(__dirname)));
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

// ======================
// STORAGE CONFIG
// ======================
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir);

const storage = multer.diskStorage({
  destination: uploadsDir,
  filename: (req, file, cb) => {
    const name = Date.now() + "-" + file.originalname;
    cb(null, name);
  }
});

const upload = multer({ storage });

// ======================
// 1. UPLOAD
// ======================
app.post("/upload", upload.single("image"), (req, res) => {
  if (!req.file) {
    logToFile("Upload failed: No file");
    return res.status(400).json({ error: "No file uploaded" });
  }

  logToFile(`File saved: ${req.file.filename}`);
  res.json({ filename: req.file.filename });
});

// ======================
// 2. GET IMAGES
// ======================
app.get("/images", (req, res) => {
  fs.readdir(uploadsDir, (err, files) => {
    if (err) {
      logToFile("Error reading uploads folder");
      return res.status(500).json({ error: "Failed to read images" });
    }
    const images = files.filter(f =>
      [".jpg", ".jpeg", ".png", ".webp"].includes(
        path.extname(f).toLowerCase()
      )
    );
    res.json({ images });
  });
});

// ======================
// 3. PREDICT
// ======================
app.post("/predict/:filename", (req, res) => {
  const filename = req.params.filename;
  const imagePath = path.join(uploadsDir, filename);

  logToFile(`PREDICT START file=${filename}`);

  if (!fs.existsSync(imagePath)) {
    logToFile(`ERROR: Image not found: ${imagePath}`);
    return res.status(404).json({ error: "Image not found" });
  }

  const inferenceScript = path.join(__dirname, "inference.py");

  exec(`python3 "${inferenceScript}" "${imagePath}"`, (err, stdout, stderr) => {
    if (err) {
      logToFile(`ERROR Python: ${stderr}`);
      return res.status(500).json({ error: "Model error", details: stderr });
    }

    const output = stdout.trim();
    logToFile(`MODEL OUTPUT: ${output}`);

    if (!output.includes("|")) {
      logToFile(`ERROR: Invalid output format: ${output}`);
      return res.status(500).json({ error: "Invalid model output" });
    }

    const [condition, cause, severity, stage, crop_type] = output.split("|");

    logToFile(`RESULT condition=${condition} cause=${cause} severity=${severity} stage=${stage} crop_type=${crop_type}`);

    res.json({ condition, cause, severity, stage, crop_type });
  });
});

// ======================
// START SERVER
// ======================
const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`🚀 Server started on port ${PORT}`);
  console.log(`📁 Uploads: ${uploadsDir}`);
  console.log(`🤖 Inference: ${path.join(__dirname, "inference.py")}`);
});