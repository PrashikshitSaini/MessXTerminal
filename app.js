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

function addMessage(message, type = "normal") {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;
  messageDiv.textContent = message;
  chatContent.appendChild(messageDiv);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function getCurrentTime() {
  const now = new Date();
  const utc = now.toUTCString();
  const ct = new Date(
    now.toLocaleString("en-US", { timeZone: "America/Chicago" })
  ).toLocaleString();
  const ist = new Date(
    now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
  ).toLocaleString();
  return `UTC: ${utc}\nCT: ${ct}\nIST: ${ist}`;
}

function showHelp() {
  const helpText = `
Available commands:
@clear - Clear the screen
@showmess - Show last 30 messages
@time - Show current time in UTC, CT, and IST
@help - Show this help message
@exit - Log out
    `.trim();
  addMessage(helpText, "system-message");
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

      // Set up message listener
      messageListener = groupRef
        .collection("messages")
        .orderBy("timestamp", "desc")
        .limit(30)
        .onSnapshot((snapshot) => {
          snapshot.docChanges().forEach((change) => {
            if (change.type === "added") {
              const data = change.doc.data();
              const message = `[${data.user}] ${data.message}`;
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
    if (message.startsWith("@")) {
      switch (message.toLowerCase()) {
        case "@clear":
          chatContent.innerHTML = "";
          return;
        case "@showmess":
          const messagesSnapshot = await db
            .collection("groups")
            .doc(currentGroup)
            .collection("messages")
            .orderBy("timestamp", "desc")
            .limit(30)
            .get();

          messagesSnapshot.forEach((doc) => {
            const data = doc.data();
            const message = `[${data.user}] ${data.message}`;
            addMessage(message);
          });
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
