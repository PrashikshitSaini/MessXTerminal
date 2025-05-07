// Firebase configuration
let firebaseConfig = {};

// Load Firebase configuration from credentials file
fetch("messxTerminalcreds.json")
  .then((response) => response.json())
  .then((config) => {
    firebaseConfig = config;
    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    // Initialize Firestore
    const db = firebase.firestore();
    // Make db available globally
    window.db = db;
  })
  .catch((error) => {
    console.error("Error loading Firebase configuration:", error);
    document.body.innerHTML =
      '<div class="error-message">Error loading Firebase configuration. Please check your credentials file.</div>';
  });
