/* ========== Page Navigation ========== */
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const target = item.dataset.page;

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${target}`).classList.add('active');
  });
});

/* ========== Chat ========== */
const messagesEl = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearChat = document.getElementById('clearChat');

function addMessage(content, role = 'assistant') {
  const msg = document.createElement('div');
  msg.className = `message ${role}`;
  msg.innerHTML = `
    <div class="message-avatar"><span>${role === 'user' ? 'U' : 'AI'}</span></div>
    <div class="message-content">
      <div class="message-bubble">${escapeHtml(content)}</div>
    </div>
  `;
  messagesEl.appendChild(msg);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return msg.querySelector('.message-bubble');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function sendMessage(question) {
  if (!question.trim()) return;

  addMessage(question, 'user');
  userInput.value = '';
  autoResize();
  sendBtn.disabled = true;

  const bubble = addMessage('', 'assistant');
  bubble.classList.add('thinking');
  bubble.textContent = '思考中...';

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question }),
    });

    if (!response.ok) throw new Error(`请求失败: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    bubble.classList.remove('thinking');
    bubble.textContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const dataStr = trimmed.slice(6);
        if (dataStr === '[DONE]') break;

        try {
          const data = JSON.parse(dataStr);
          if (data.error) {
            fullText = `调用失败: ${data.error}`;
            bubble.textContent = fullText;
            break;
          }
          const token = data.content || '';
          if (token) {
            fullText += token;
            bubble.textContent = fullText;
            messagesEl.scrollTop = messagesEl.scrollHeight;
          }
        } catch (e) {
          // skip parse errors
        }
      }
    }

    if (!fullText) {
      bubble.textContent = '未收到回复，请稍后重试。';
    }
  } catch (err) {
    bubble.classList.remove('thinking');
    bubble.textContent = `连接失败: ${err.message}`;
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}

chatForm.addEventListener('submit', e => {
  e.preventDefault();
  sendMessage(userInput.value);
});

userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

function autoResize() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}
userInput.addEventListener('input', autoResize);

clearChat.addEventListener('click', () => {
  messagesEl.innerHTML = '';
  addMessage('对话已清空。有什么可以帮你的吗？');
});

/* ========== Quick Actions ========== */
document.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    sendMessage(btn.dataset.q);
  });
});

/* ========== Health Check ========== */
async function checkHealth() {
  const statusDot = document.querySelector('.status-dot');
  const statusText = document.getElementById('statusText');
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.status === 'ok') {
      statusDot.classList.add('online');
      statusText.textContent = '已连接';
    } else {
      statusDot.classList.remove('online');
      statusText.textContent = '异常';
    }
  } catch {
    statusDot.classList.remove('online');
    statusText.textContent = '未连接';
  }
}

checkHealth();
setInterval(checkHealth, 30000);
