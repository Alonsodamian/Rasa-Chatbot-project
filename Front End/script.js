document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
      addMessage("Bot: Halo! Selamat datang di layanan kami. Ada yang bisa saya bantu hari ini? 😊", "bot");
    }, 500);
  });
  
  const chatWindow = document.getElementById("chat-window");
  const inputBox = document.getElementById("input-box");
  const sendButton = document.getElementById("send-button");

  function addMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = message;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
  
  function sendMessage() {
    const message = inputBox.value.trim();
    if (message === "") return;
  
    addMessage(`Anda: ${message}`, "user");
    inputBox.value = "";
  
    fetch("http://localhost:5005/webhooks/rest/webhook", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender: "user", message: message }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.length === 0) {
          addMessage("Bot tidak merespon.", "bot");
        }
        data.forEach((item) => {
          if (item.text) {
            addMessage(`Bot: ${item.text}`, "bot");
          }
        });
      })
      .catch((error) => {
        console.error("Error:", error);
        addMessage("Terjadi kesalahan menghubungi server.", "bot");
      });
  }
  
  sendButton.addEventListener("click", sendMessage);
  
  inputBox.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault(); 
      sendMessage();
    }
  });
  