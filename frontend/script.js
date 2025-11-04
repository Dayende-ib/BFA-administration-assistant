const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// Store conversation history
let conversationHistory = [];

// Apply saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
  }
});

const sendMessage = async (question) => {
  if (!question) question = input.value.trim();
  if (!question) return;

  // Add user message to chat with avatar
  const userMessage = document.createElement('div');
  userMessage.className = 'message user';
  userMessage.innerHTML = `
    <div class="message-content">
      <div class="message-text">${question}</div>
    </div>
  `;
  chat.appendChild(userMessage);

  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  // Add loading indicator with avatar
  const botMessage = document.createElement('div');
  botMessage.className = 'message bot';
  botMessage.innerHTML = `
    <div class="avatar">
      <i class="fas fa-robot"></i>
    </div>
    <div class="message-content">
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
  chat.appendChild(botMessage);
  chat.scrollTop = chat.scrollHeight;

  try {
    // Call the backend API
    const response = await fetch('/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        top_k: 5
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Format the response with answer and sources
    let responseHTML = `
      <div class="avatar">
        <i class="fas fa-robot"></i>
      </div>
      <div class="message-content">
        <div class="message-text">${data.answer}</div>
    `;
    
    if (data.sources && data.sources.length > 0) {
      responseHTML += `
        <div class="sources">
          <strong>Sources:</strong>
          ${data.sources.map(source => 
            `<div style="margin: 5px 0;">• <a href="${source.url}" target="_blank">${source.titre}</a></div>`
          ).join('')}
        </div>
      `;
    }
    
    // Add feedback buttons
    responseHTML += `
        <div class="feedback">
          <span>Cette réponse vous a-t-elle aidé ?</span>
          <button class="feedback-btn" onclick="sendFeedback('positive')" title="Utile">👍</button>
          <button class="feedback-btn" onclick="sendFeedback('negative')" title="Pas utile">👎</button>
        </div>
      </div>
    `;
    
    botMessage.innerHTML = responseHTML;
    
    // Add to conversation history
    conversationHistory.push({
      question: question,
      answer: data.answer,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error:', error);
    botMessage.innerHTML = `
      <div class="avatar">
        <i class="fas fa-robot"></i>
      </div>
      <div class="message-content">
        <div class="message-text">Désolé, une erreur s'est produite lors de la récupération de la réponse. Veuillez réessayer.</div>
      </div>
    `;
  }
  
  chat.scrollTop = chat.scrollHeight;
};

// Function to send feedback
const sendFeedback = (feedback) => {
  console.log('Feedback received:', feedback);
  // In a real implementation, you would send this to your backend
  // Show a confirmation message
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