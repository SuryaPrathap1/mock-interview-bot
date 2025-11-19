document.addEventListener("DOMContentLoaded", () => {

  const sessionId = document.getElementById("session_id").value;

 
  const typeButtons = document.querySelectorAll(".select-btn");
  const startBtn = document.getElementById("start-btn");
  const resetBtn = document.getElementById("reset-btn");
  const topicWrap = document.getElementById("topic-wrap");
  const topicSelect = document.getElementById("topic");

  const chatArea = document.getElementById("chat-area");
  const chatBox = document.getElementById("chat-box");
  const answerInput = document.getElementById("answer-input");

  const recStart = document.getElementById("rec-start");
  const recStop = document.getElementById("rec-stop");
  const recIndicator = document.getElementById("rec-indicator");

  const sendBtn = document.getElementById("send-btn");
  const exitBtn = document.getElementById("exit-btn");

  let selectedType = null;
  let recognition = null;
  let isRecording = false;

  
  typeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      typeButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      selectedType = btn.dataset.type;

      topicWrap.classList.toggle("hidden", selectedType !== "TR");

      startBtn.disabled = false;
    });
  });

  resetBtn.addEventListener("click", () => {
    typeButtons.forEach(b => b.classList.remove("active"));
    selectedType = null;
    topicWrap.classList.add("hidden");
    startBtn.disabled = true;
  });

 
  startBtn.addEventListener("click", async () => {
    const payload = {
      session_id: sessionId,
      type: selectedType,
      topic: selectedType === "TR" ? topicSelect.value : null
    };

    const res = await fetch("/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    chatArea.classList.remove("hidden");

    if (data.question) {
      addMessage(data.question, "assistant");
      speak(data.question);
    }
  });


  if (window.SpeechRecognition || window.webkitSpeechRecognition) {
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;

    recognition = new Rec();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = true;

    recognition.onresult = event => {
      let text = event.results[event.resultIndex][0].transcript.trim();
      if (text) {
        addMessage(text, "user");
        sendAnswer(text);
      }
    };

    
    recognition.onend = () => {
      if (isRecording) {
        recognition.start();  
      }
    };
  }

  recStart.addEventListener("click", () => {
    isRecording = true;
    recognition.start();
    startRecUI();
  });

  recStop.addEventListener("click", () => {
    isRecording = false;
    recognition.stop();
    stopRecUI();
  });

  function startRecUI() {
    recIndicator.classList.remove("hidden");
    recStart.classList.add("hidden");
    recStop.classList.remove("hidden");
  }

  function stopRecUI() {
    recIndicator.classList.add("hidden");
    recStart.classList.remove("hidden");
    recStop.classList.add("hidden");
  }

  
  sendBtn.addEventListener("click", () => {
    const text = answerInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    answerInput.value = "";

    sendAnswer(text);
  });

  exitBtn.addEventListener("click", () => {
    addMessage("end interview", "user");
    sendAnswer("end interview");
  });

  
  async function sendAnswer(text) {
    const res = await fetch("/answer", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ session_id: sessionId, answer: text })
    });

    const data = await res.json();

    if (data.final) {
      addMessage("Interview Summary:", "assistant");
      addMessage(data.summary, "assistant");
      speak(data.summary);
      return;
    }

    if (data.feedback) addMessage(data.feedback, "feedback");
    if (data.next_question) {
      addMessage(data.next_question, "assistant");
      speak(data.next_question);
    }
  }

  
  function addMessage(text, role) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.innerHTML = text.replace(/\n/g, "<br>");
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

 
  function speak(text) {
    const utter = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.cancel();

    setTimeout(() => {
      window.speechSynthesis.speak(utter);
    }, 100);
  }

});
