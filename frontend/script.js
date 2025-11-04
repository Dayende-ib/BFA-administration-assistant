const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

const sendMessage = (question) => {
  if (!question) question = input.value.trim();
  if (!question) return;

  const userMsg = document.createElement('div');
  userMsg.className = 'message user';
  userMsg.textContent = question;
  chat.appendChild(userMsg);

  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  const botMsg = document.createElement('div');
  botMsg.className = 'message bot';
  botMsg.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Recherche en cours...`;
  chat.appendChild(botMsg);
  chat.scrollTop = chat.scrollHeight;

  setTimeout(() => {
    let response = "";
    if (question.includes("naissance") && !question.includes("déclarer")) {
      response = `<strong>Acte de naissance</strong><br>• Gratuit<br>• 7 jours<br>• CNI + extrait<br><a href="#" style="color:#009A44;">Lien</a>`;
    } else if (question.includes("casier")) {
      response = `<strong>Casier judiciaire</strong><br>• 500 FCFA<br>• 5 jours<br>• CNI<br><a href="#" style="color:#009A44;">Lien</a>`;
    } else if (question.includes("résidence")) {
      response = `<strong>Certificat de résidence</strong><br>• 200 FCFA<br>• 48h<br>• CNI + preuve<br><a href="#" style="color:#009A44;">Lien</a>`;
    } else if (question.includes("déclarer")) {
      response = `<strong>Déclaration naissance</strong><br>• Gratuit<br>• 60 jours<br>• Certificat médical<br><a href="#" style="color:#009A44;">Lien</a>`;
    } else {
      response = `Aucune info pour : "<strong>${question}</strong>"`;
    }
    botMsg.innerHTML = response;
    chat.scrollTop = chat.scrollHeight;
  }, 1800);
};

const askQuestion = (q) => {
  input.value = q;
  sendMessage(q);
};

sendBtn.addEventListener('click', () => sendMessage());
input.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMessage();
});