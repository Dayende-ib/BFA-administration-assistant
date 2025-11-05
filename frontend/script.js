const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// URL de l'API backend
const API_BASE_URL = "http://localhost:8000";

// Initialisation du thème (mode clair/sombre)
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
  }
});

/**
 * Formate la réponse de l'API en HTML structuré
 * @param {string} answer - Réponse brute de l'API
 * @returns {string} - HTML formaté
 */
function formatApiAnswer(answer) {
  // Si la réponse n'est pas structurée, on la retourne telle quelle
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
      html += `<p style="margin-bottom: 8px;"><strong>${parts[0].trim()} :</strong> ${parts[1].trim()}</p>`;
    } else if (line.trim()) {
      // Pour les lignes sans ':', on les affiche simplement
      html += `<p>${line}</p>`;
    }
  });
  
  return html;
}

/**
 * Envoie un message à l'API et affiche la réponse
 * @param {string} question - Question de l'utilisateur
 */
const sendMessage = async (question) => {
  // Récupère la question depuis l'input si non fournie
  if (!question) question = input.value.trim();
  if (!question) return;

  // Affiche le message de l'utilisateur dans l'interface
  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `<div class="message-content"><div class="message-text">${question}</div></div>`;
  chat.appendChild(userMessage);
  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  // Affiche l'indicateur de chargement
  const botMessage = document.createElement('div');
  botMessage.className = 'message bot';
  botMessage.innerHTML = `<div class="avatar"><i class="fas fa-robot"></i></div><div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
  chat.appendChild(botMessage);
  chat.scrollTop = chat.scrollHeight;

  try {
    // Envoie la requête à l'API
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        top_k: 5 // Cet argument est ignoré par le backend qui force top_k=1
      })
    });

    // Vérifie si la requête a réussi
    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Erreur HTTP! status: ${response.status}. Réponse: ${errorData}`);
    }

    // Récupère et traite la réponse
    const data = await response.json();
    
    // Formate la réponse avant de l'afficher
    const formattedAnswer = formatApiAnswer(data.answer);
    
    // Construit le HTML de la réponse
    let responseHTML = `
      <div class="avatar">
        <i class="fas fa-robot"></i>
      </div>
      <div class="message-content">
        <div class="message-text">${formattedAnswer}</div>
    `;
    
    // Ajoute les sources si disponibles
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
    
    // Ajoute les boutons de feedback
    responseHTML += `
        <div class="feedback">
          <span>Cette réponse vous a-t-elle aidé ?</span>
          <button class="feedback-btn" onclick="sendFeedback('positive')" title="Utile">👍</button>
          <button class="feedback-btn" onclick="sendFeedback('negative')" title="Pas utile">👎</button>
        </div>
      </div>
    `;
    
    // Affiche la réponse dans l'interface
    botMessage.innerHTML = responseHTML;

  } catch (error) {
    // Gère les erreurs de connexion
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
  
  // Fait défiler vers le bas
  chat.scrollTop = chat.scrollHeight;
};

/**
 * Envoie un feedback sur la réponse
 * @param {string} feedback - Type de feedback ('positive' ou 'negative')
 */
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

/**
 * Pose une question prédéfinie
 * @param {string} q - Question à poser
 */
const askQuestion = (q) => {
  input.value = q;
  sendMessage(q);
};

// Écouteurs d'événements
sendBtn.addEventListener('click', () => sendMessage());
input.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMessage();
});