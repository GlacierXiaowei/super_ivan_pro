const eventsList = document.getElementById('events-list');
const statusNode = document.getElementById('status');
const saveStatusNode = document.getElementById('save-status');
const refreshButton = document.getElementById('refresh-events');
const reloadButton = document.getElementById('reload-rule');
const form = document.getElementById('rule-form');

const CHAT_SCOPE_LABELS = {
  any: '不限',
  group: '仅群聊',
  private: '仅私聊',
};

const MESSAGE_TYPE_LABELS = {
  text: '文本',
  emoji: '表情',
  image: '图片',
  voice: '语音',
  video: '视频',
  link: '链接或文件',
  unknown: '不限',
};

function getChatScopeLabel(value) {
  return CHAT_SCOPE_LABELS[value] || value || '未知范围';
}

function getMessageTypeLabel(value) {
  return MESSAGE_TYPE_LABELS[value] || value || '未知类型';
}

function formDataToRule() {
  const data = new FormData(form);
  const replies = String(data.get('replies') || '')
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    id: String(data.get('id') || 'web_console_rule').trim() || 'web_console_rule',
    enabled: String(data.get('enabled')) === 'true',
    talker: String(data.get('talker') || '').trim(),
    sender: String(data.get('sender') || '').trim(),
    chat_scope: String(data.get('chat_scope') || 'any'),
    type: String(data.get('type') || 'text'),
    match_mode: String(data.get('match_mode') || 'exact'),
    pattern: String(data.get('pattern') || ''),
    cooldown_ms: Number(data.get('cooldown_ms') || 0),
    replies,
  };
}

function applyRuleToForm(rule) {
  form.elements.id.value = rule.id || 'web_console_rule';
  form.elements.enabled.value = String(rule.enabled ?? true);
  form.elements.talker.value = rule.talker || '';
  form.elements.sender.value = rule.sender || '';
  form.elements.chat_scope.value = rule.chat_scope || 'any';
  form.elements.type.value = rule.type || 'text';
  form.elements.match_mode.value = rule.match_mode || 'exact';
  form.elements.pattern.value = rule.pattern || '';
  form.elements.cooldown_ms.value = String(rule.cooldown_ms ?? 0);
  form.elements.replies.value = Array.isArray(rule.replies) ? rule.replies.join('\n') : '';
}

function applyEventToForm(event) {
  form.elements.talker.value = event.talker_name || event.talker || '';
  form.elements.sender.value = event.sender_name || event.sender || '';
  form.elements.chat_scope.value = event.chat_scope || (event.is_chat_room ? 'group' : 'private');
  form.elements.type.value = event.type || 'text';
  form.elements.pattern.value = event.content || '';
  saveStatusNode.textContent = '已从事件带入规则字段，尚未保存。';
}

function renderEvents(events) {
  eventsList.innerHTML = '';
  if (!events.length) {
    statusNode.textContent = '当前没有拿到最近事件。';
    return;
  }

  statusNode.textContent = `最近事件 ${events.length} 条`;
  for (const event of events) {
    const card = document.createElement('article');
    card.className = 'event-card';
    card.innerHTML = `
      <header>
        <strong>${event.talker_name || event.talker || '（未知对象）'}</strong>
      </header>
      <div class="event-meta">
        <span class="badge">${getChatScopeLabel(event.chat_scope || (event.is_chat_room ? 'group' : 'private'))}</span>
        <span class="badge">${getMessageTypeLabel(event.type || 'unknown')}</span>
        <span>发送者: ${event.sender_name || event.sender || '（空）'}</span>
        <span>时间: ${event.timestamp || '-'}</span>
      </div>
      <div class="event-content">${event.content || '（空内容）'}</div>
    `;

    const useButton = document.createElement('button');
    useButton.type = 'button';
    useButton.className = 'secondary';
    useButton.textContent = '用这条事件带入规则';
    useButton.addEventListener('click', () => applyEventToForm(event));

    card.appendChild(document.createElement('div')).appendChild(useButton);
    eventsList.appendChild(card);
  }
}

async function loadEvents() {
  statusNode.textContent = '正在刷新事件...';
  try {
    const response = await fetch('/api/events?limit=40');
    if (!response.ok) {
      throw new Error(`events ${response.status}`);
    }
    const events = await response.json();
    renderEvents(events);
  } catch (error) {
    statusNode.textContent = `事件加载失败: ${error.message}`;
  }
}

async function loadRules() {
  saveStatusNode.textContent = '正在读取规则...';
  try {
    const response = await fetch('/api/rules');
    if (!response.ok) {
      throw new Error(`rules ${response.status}`);
    }
    const rules = await response.json();
    if (Array.isArray(rules) && rules.length > 0) {
      applyRuleToForm(rules[0]);
      saveStatusNode.textContent = '已读取现有规则。';
    } else {
      saveStatusNode.textContent = '规则文件为空，等待你保存第一条规则。';
    }
  } catch (error) {
    saveStatusNode.textContent = `规则读取失败: ${error.message}`;
  }
}

async function saveRules(event) {
  event.preventDefault();
  const payload = [formDataToRule()];
  saveStatusNode.textContent = '正在保存规则...';
  try {
    const response = await fetch('/api/rules', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`save ${response.status}`);
    }
    saveStatusNode.textContent = '规则已保存到本地文件。';
  } catch (error) {
    saveStatusNode.textContent = `规则保存失败: ${error.message}`;
  }
}

refreshButton.addEventListener('click', loadEvents);
reloadButton.addEventListener('click', loadRules);
form.addEventListener('submit', saveRules);

loadRules();
loadEvents();
window.setInterval(loadEvents, 3000);
