// Global variables
let currentUser = "";
let currentGroup = "";
let messageListener = null;

// DOM Elements
const loginScreen = document.getElementById("login-screen");
const chatScreen = document.getElementById("chat-screen");
const userNameInput = document.getElementById("user-name");
const groupNameInput = document.getElementById("group-name");
const groupList = document.getElementById("group-list");
const groupsList = document.getElementById("groups-list");
const chatContent = document.getElementById("chat-content");
const messageInput = document.getElementById("message-input");
const userPrompt = document.getElementById("user-prompt");
const currentGroupSpan = document.getElementById("current-group");

// Event Listeners
userNameInput.addEventListener("keypress", handleNameInput);
groupNameInput.addEventListener("keypress", handleGroupInput);
messageInput.addEventListener("keypress", handleMessageInput);

// Helper Functions
function showScreen(screen) {
  loginScreen.classList.add("hidden");
  chatScreen.classList.add("hidden");
  screen.classList.remove("hidden");
}

function formatTimestamp(timestamp) {
  if (!timestamp) return "";
  const date = timestamp.toDate();
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const year = date.getFullYear().toString().slice(-2);
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `[${day}:${month}:${year} ${hours}:${minutes}]`;
}

function addMessage(message, type = "normal") {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;

  // For help/command lines, add .command class for styling
  if (
    type === "system-message" &&
    (message.includes("clear -") ||
      message.includes("@showmess") ||
      message.includes("@time") ||
      message.includes("@help") ||
      message.includes("@exit"))
  ) {
    messageDiv.classList.add("command");
  }

  messageDiv.textContent = message;
  chatContent.appendChild(messageDiv);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function getCurrentTime() {
  const now = new Date();
  const utc = now.toUTCString().split(" ")[4]; // Get just the time part
  const ct = new Date(
    now.toLocaleString("en-US", { timeZone: "America/Chicago" })
  ).toLocaleTimeString("en-US", { hour12: false });
  const ist = new Date(
    now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
  ).toLocaleTimeString("en-US", { hour12: false });
  return `UTC: ${utc} | CT: ${ct} | IST: ${ist}`;
}

function showHelp() {
  const commands = [
    "clear - Clear the screen",
    "@showmess - Show last 30 messages",
    "@time - Show current time in UTC, CT, and IST",
    "@help - Show this help message",
    "@exit - Log out",
  ];

  addMessage("Available commands:", "system-message");
  commands.forEach((cmd) => addMessage(cmd, "system-message"));
}

// Event Handlers
function handleNameInput(e) {
  if (e.key === "Enter") {
    const name = userNameInput.value.trim();
    if (name) {
      currentUser = name;
      userNameInput.parentElement.classList.add("hidden");
      groupNameInput.parentElement.classList.remove("hidden");
      groupNameInput.focus();
    }
  }
}

async function handleGroupInput(e) {
  if (e.key === "Enter") {
    const groupInput = groupNameInput.value.trim();

    if (groupInput.toLowerCase() === "list") {
      // Show existing groups
      const groupsSnapshot = await db.collection("groups").get();
      groupsList.innerHTML = "";
      groupsSnapshot.forEach((doc) => {
        const li = document.createElement("li");
        li.textContent = doc.id;
        li.onclick = () => {
          groupNameInput.value = doc.id;
          handleGroupInput({ key: "Enter" });
        };
        groupsList.appendChild(li);
      });
      groupList.classList.remove("hidden");
      return;
    }

    if (groupInput) {
      currentGroup = groupInput;
      const groupRef = db.collection("groups").doc(currentGroup);

      // Check if group exists
      const groupDoc = await groupRef.get();
      if (!groupDoc.exists) {
        // Create new group
        await groupRef.set({
          created: firebase.firestore.FieldValue.serverTimestamp(),
        });
        addMessage(`Created new group: ${currentGroup}`, "system-message");
      }

      // Show chat screen
      showScreen(chatScreen);
      currentGroupSpan.textContent = currentGroup;
      userPrompt.textContent = `${currentUser}> `;
      messageInput.focus();

      // --- FIX: Clear chat and only listen for new messages ---
      chatContent.innerHTML = "";
      addMessage("use @help to know your hacker powers", "system-message");
      if (messageListener) messageListener(); // Unsubscribe previous listener if any
      let latestTimestamp = null;
      // Listen for new messages only (not history)
      messageListener = groupRef
        .collection("messages")
        .orderBy("timestamp", "asc")
        .where("timestamp", ">", new Date())
        .onSnapshot((snapshot) => {
          snapshot.docChanges().forEach((change) => {
            if (change.type === "added") {
              const data = change.doc.data();
              const timestamp = formatTimestamp(data.timestamp);
              const prefix = timestamp ? `${timestamp} ` : "";
              const message = `${prefix}[${data.user}] ${data.message}`;
              addMessage(message);
            }
          });
        });
    }
  }
}

async function handleMessageInput(e) {
  if (e.key === "Enter") {
    const message = messageInput.value.trim();
    messageInput.value = "";

    if (!message) return;

    // Handle commands
    if (message.toLowerCase() === "clear") {
      chatContent.innerHTML = "";
      return;
    }

    if (message.startsWith("@")) {
      switch (message.toLowerCase()) {
        case "@clear":
          chatContent.innerHTML = "";
          return;
        case "@showmess":
          addMessage("***** Showing past messages *****", "system-message");
          if (!window.db || !currentGroup) {
            addMessage(
              "Error: Database not ready or group not selected.",
              "error-message"
            );
            return;
          }
          const messagesSnapshot = await db
            .collection("groups")
            .doc(currentGroup)
            .collection("messages")
            .orderBy("timestamp", "desc")
            .limit(30)
            .get();

          const messages = [];
          messagesSnapshot.forEach((doc) => {
            const data = doc.data();
            const timestamp = formatTimestamp(data.timestamp);
            const prefix = timestamp ? `${timestamp} ` : "";
            messages.unshift(`${prefix}[${data.user}] ${data.message}`);
          });
          messages.forEach((msg) => addMessage(msg));
          addMessage("***** End of message history *****", "system-message");
          return;
        case "@time":
          addMessage(getCurrentTime(), "system-message");
          return;
        case "@help":
          showHelp();
          return;
        case "@exit":
          if (messageListener) {
            messageListener();
          }
          showScreen(loginScreen);
          userNameInput.value = "";
          groupNameInput.value = "";
          userNameInput.parentElement.classList.remove("hidden");
          groupNameInput.parentElement.classList.add("hidden");
          groupList.classList.add("hidden");
          chatContent.innerHTML = "";
          return;
      }
    }

    // --- FIX: Check for db, currentUser, currentGroup ---
    if (!window.db) {
      addMessage("Error: Database not ready.", "error-message");
      return;
    }
    if (!currentUser) {
      addMessage("Error: User not set.", "error-message");
      return;
    }
    if (!currentGroup) {
      addMessage("Error: Group not set.", "error-message");
      return;
    }

    // Send message
    try {
      await db
        .collection("groups")
        .doc(currentGroup)
        .collection("messages")
        .add({
          message: message,
          user: currentUser,
          timestamp: firebase.firestore.FieldValue.serverTimestamp(),
        });
    } catch (error) {
      addMessage(`Error sending message: ${error.message}`, "error-message");
    }
  }
}

// Initialize
showScreen(loginScreen);
userNameInput.focus();
