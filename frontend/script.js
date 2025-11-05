const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// --- URL de votre API (Backend) ---
const API_BASE_URL = "http://localhost:8000";

// ... (Le code pour le dark mode reste le même) ...
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
  }
});

// ==========================================================
// NOUVELLE FONCTION : Formatage de la réponse
// ==========================================================
/**
 * Prend la réponse brute de l'API (un seul bloc de texte)
 * et la transforme en HTML structuré.
 */
function formatApiAnswer(answer) {
  // Si la réponse n'est pas structurée (ex: "Aucune information..."),
  // on la retourne telle quelle, mais en protégeant contre le HTML.
  if (!answer.includes('Pièces à fournir')) {
     // Convertit les sauts de ligne simples en <br>
     return answer.replace(/\n/g, '<br>');
  }

  let html = '';
  // Sépare la réponse par lignes, et filtre les lignes vides
  const lines = answer.split('\n').filter(line => line.trim() !== '');
  
  lines.forEach(line => {
    // Sépare la ligne au premier deux-points (:)
    const parts = line.split(/:(.+)/); // Regex pour [Clé] et [Valeur]
    
    if (parts.length === 2) {
      // Si on a une Clé:Valeur, on met la clé en gras
      // On utilise <p> pour garantir le saut de ligne
      html += `<p style="margin-bottom: 8px;"><strong>${parts[0].trim()} :</strong> ${parts[1].trim()}</p>`;
    } else if (line.trim()) {
      // Pour les lignes sans ':', on les affiche simplement (sécurité)
      html += `<p>${line}</p>`;
    }
  });
  
  return html;
}
// ==========================================================

const sendMessage = async (question) => {
  if (!question) question = input.value.trim();
  if (!question) return;

  // (Affichage du message utilisateur - inchangé)
  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `<div class="message-content"><div class="message-text">${question}</div></div>`;
  chat.appendChild(userMessage);
  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  // (Affichage du loader - inchangé)
  const botMessage = document.createElement('div');
  botMessage.className = 'message bot';
  botMessage.innerHTML = `<div class="avatar"><i class="fas fa-robot"></i></div><div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
  chat.appendChild(botMessage);
  chat.scrollTop = chat.scrollHeight;

  try {
    
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        top_k: 5 // (Cet argument est ignoré par le backend qui force top_k=1)
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Erreur HTTP! status: ${response.status}. Réponse: ${errorData}`);
    }

    const data = await response.json();
    
    // --- MODIFICATION ICI ---
    // On formate la réponse AVANT de l'afficher
    const formattedAnswer = formatApiAnswer(data.answer);
    // -------------------------
    
    let responseHTML = `
      <div class="avatar">
        <i class="fas fa-robot"></i>
      </div>
      <div class="message-content">
        <div class="message-text">${formattedAnswer}</div>
    `;
    
    // (Le reste : gestion des sources et du feedback - inchangé)
    if (data.sources && data.sources.length > 0) {
      responseHTML += `
        <div class="sources">
          <strong>Sources:</strong>
          ${data.sources.map(source => 
            (source.url && source.url !== '#' && source.url !== 'Non spécifié')
              ? `<div style="margin: 5px 0;">• <a href="${source.url}" target="_blank">${source.titre}</a></div>`
              : `<div style="margin: 5px 0;">• ${source.titre}</div>`
          ).join('')}
        </div>
      `;
    }
    
    responseHTML += `
        <div class="feedback">
          <span>Cette réponse vous a-t-elle aidé ?</span>
          <button class="feedback-btn" onclick="sendFeedback('positive')" title="Utile">👍</button>
          <button class="feedback-btn" onclick="sendFeedback('negative')" title="Pas utile">👎</button>
        </div>
      </div>
    `;
    
    botMessage.innerHTML = responseHTML;

  } catch (error) {
    console.error('Error:', error);
    botMessage.innerHTML = `
      <div class="avatar">
        <i class="fas fa-robot"></i>
      </div>
      <div class="message-content">
        <div class="message-text">Désolé, une erreur s'est produite lors de la connexion à l'API. (Détails: ${error.message})</div>
      </div>
    `;
  }
  
  chat.scrollTop = chat.scrollHeight;
};

// (Le reste de script.js : sendFeedback, askQuestion, listeners... reste inchangé)
// ...
const sendFeedback = (feedback) => {
  console.log('Feedback received:', feedback);
  const confirmation = document.createElement('div');
  confirmation.className = 'message bot';
  confirmation.innerHTML = `
    <div class="avatar">
      <i class="fas fa-robot"></i>
    </div>
    <div class="message-content">
      <div class="message-text">
        ${feedback === 'positive' 
          ? 'Merci pour votre feedback positif !' 
          : 'Merci pour votre feedback. Nous allons essayer de nous améliorer.'}
      </div>
    </div>
  `;
  chat.appendChild(confirmation);
  chat.scrollTop = chat.scrollHeight;
};

const askQuestion = (q) => {
  input.value = q;
  sendMessage(q);
};

sendBtn.addEventListener('click', () => sendMessage());
input.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMessage();
});