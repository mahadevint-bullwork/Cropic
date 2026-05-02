import {
  View,
  Text,
  TouchableOpacity,
  Image,
  StyleSheet,
  ActivityIndicator,
  ScrollView
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useState, useEffect } from 'react';

export default function HomeScreen() {

  const [image, setImage] = useState<string | null>(null);
  const [prediction, setPrediction] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);

  // ✅ NEW STATE
  const [details, setDetails] = useState({
    cause: "",
    severity: "",
    stage: ""
  });

  const [loading, setLoading] = useState(false);

  // 🆕 HISTORY STATE
  const [historyImages, setHistoryImages] = useState<string[]>([]);

  const BASE_URL = "http://192.168.0.131:3000";

  // ======================
  // 🆕 FETCH HISTORY
  // ======================
  const fetchImages = async () => {
    try {
      const res = await fetch(`${BASE_URL}/images`);
      const data = await res.json();

      setHistoryImages(data.images);
    } catch (err) {
      console.log("Error fetching images", err);
    }
  };

  // Load once on app start
  useEffect(() => {
    fetchImages();
  }, []);

  // ======================
  // GALLERY
  // ======================
  const pickImage = async () => {
    let res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (!res.canceled) {
      setImage(res.assets[0].uri);
      setPrediction("");
      setConfidence(null);

      // reset details
      setDetails({
        cause: "",
        severity: "",
        stage: ""
      });
    }
  };

  // ======================
  // CAMERA
  // ======================
  const openCamera = async () => {
    let res = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (!res.canceled) {
      setImage(res.assets[0].uri);
      setPrediction("");
      setConfidence(null);

      // reset details
      setDetails({
        cause: "",
        severity: "",
        stage: ""
      });
    }
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

    formData.append("image", {
      uri: image,
      name: "photo.jpg",
      type: "image/jpeg"
    } as any);

    try {
      // Upload
      const uploadRes = await fetch(`${BASE_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const uploadData = await uploadRes.json();
      const filename = uploadData.filename;

      // Predict
      const predictRes = await fetch(`${BASE_URL}/predict/${filename}`, {
        method: "POST"
      });

      const predictData = await predictRes.json();

      console.log(predictData); // ✅ debug

      // ✅ UPDATED MAPPING
      setPrediction(predictData.condition);

      setDetails({
        cause: predictData.cause,
        severity: predictData.severity,
        stage: predictData.stage
      });

      setConfidence(null); // no longer used

      // 🆕 REFRESH HISTORY AFTER UPLOAD
      fetchImages();

    } catch (err) {
      console.error(err);
      alert("Error occurred");
    }

    setLoading(false);
  };

  return (
    <ScrollView style={styles.container}>

      <Text style={styles.title}>🌿 Crop Health Analyzer</Text>

      {/* IMAGE */}
      <View style={styles.card}>
        {image ? (
          <Image
            key={image}
            source={{ uri: image }}
            style={styles.image}
          />
        ) : (
          <Text>No Image Selected</Text>
        )}
      </View>

      {/* BUTTONS */}
      <View style={styles.row}>
        <TouchableOpacity style={styles.btn} onPress={openCamera}>
          <Text style={styles.btnText}>📷 Camera</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btn} onPress={pickImage}>
          <Text style={styles.btnText}>🖼 Gallery</Text>
        </TouchableOpacity>
      </View>

      {/* ANALYZE */}
      <TouchableOpacity style={styles.predictBtn} onPress={uploadAndPredict}>
        <Text style={styles.btnText}>🔍 Analyze</Text>
      </TouchableOpacity>

      {loading && <ActivityIndicator size="large" />}

      {/* RESULT */}
      {prediction !== "" && !loading && (
        <View style={styles.resultCard}>
          <Text>Condition: {prediction}</Text>
          <Text>Cause: {details.cause}</Text>
          <Text>Severity: {details.severity}</Text>
          <Text>Stage: {details.stage}</Text>
        </View>
      )}

      {/* ======================
          🆕 HISTORY SECTION
         ====================== */}
      <Text style={styles.historyTitle}>🕘 History</Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {historyImages.map((img, index) => (
          <Image
            key={index}
            source={{ uri: `${BASE_URL}/uploads/${img}` }}
            style={styles.historyImage}
          />
        ))}
      </ScrollView>

    </ScrollView>
  );
}

// ======================
const styles = StyleSheet.create({

  container: {
    flex: 1,
    padding: 20
  },

  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
    textAlign: "center"
  },

  card: {
    height: 200,
    backgroundColor: "#eee",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 20
  },

  image: {
    width: "100%",
    height: "100%"
  },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10
  },

  btn: {
    backgroundColor: "green",
    padding: 10,
    borderRadius: 8
  },

  predictBtn: {
    backgroundColor: "darkgreen",
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 20
  },

  btnText: {
    color: "white"
  },

  resultCard: {
    padding: 10,
    backgroundColor: "#fff",
    marginBottom: 20
  },

  historyTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10
  },

  historyImage: {
    width: 100,
    height: 100,
    marginRight: 10,
    borderRadius: 8
  }

});