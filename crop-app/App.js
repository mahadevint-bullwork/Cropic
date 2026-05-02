import { View, Text, Button, Image, StyleSheet } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';

export default function App() {

  const [image, setImage] = useState(null);
  const [result, setResult] = useState("");

  // 🔥 CHANGE THIS TO YOUR IP
  const BASE_URL = "http://192.168.0.115:3000";

  // Pick image
  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  // Upload + Predict
  const uploadAndPredict = async () => {

    if (!image) {
      alert("Pick an image first");
      return;
    }

    setResult("Uploading...");

    const formData = new FormData();

    formData.append("image", {
      uri: image,
      name: "photo.jpg",
      type: "image/jpeg"
    });

    try {
      // Step 1: Upload
      const uploadRes = await fetch(`${BASE_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const uploadData = await uploadRes.json();

      const filename = uploadData.filename;

      setResult("Processing...");

      // Step 2: Predict
      const predictRes = await fetch(`${BASE_URL}/predict/${filename}`, {
        method: "POST"
      });

      const predictData = await predictRes.json();

      setResult(
        `Prediction: ${predictData.prediction}\nConfidence: ${(predictData.confidence * 100).toFixed(2)}%`
      );

    } catch (err) {
      console.error(err);
      setResult("Error occurred");
    }
  };

  return (
    <View style={styles.container}>

      <Text style={styles.title}>🌿 Crop Health Detection</Text>

      <Button title="Pick Image" onPress={pickImage} />

      {image && (
        <Image source={{ uri: image }} style={styles.image} />
      )}

      <Button title="Predict" onPress={uploadAndPredict} />

      <Text style={styles.result}>{result}</Text>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20
  },
  title: {
    fontSize: 20,
    marginBottom: 20
  },
  image: {
    width: 250,
    height: 250,
    marginVertical: 20,
    borderRadius: 10
  },
  result: {
    marginTop: 20,
    fontSize: 16,
    textAlign: 'center'
  }
});