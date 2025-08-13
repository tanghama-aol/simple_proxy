async function loadRules() {
    const response = await fetch('/api/rules');
    const rules = await response.json();
    const rulesList = document.getElementById('rulesList');
    rulesList.innerHTML = '';
    
    rules.forEach(rule => {
        const ruleElement = document.createElement('div');
        ruleElement.className = 'rule-item';
        ruleElement.innerHTML = `
            <span>${rule.pattern} → ${rule.action}${rule.proxy ? ` (${rule.proxy})` : ''}</span>
            <button class="delete-rule" onclick="deleteRule('${rule.pattern}')">Delete</button>
        `;
        rulesList.appendChild(ruleElement);
    });
}

async function loadConfig() {
    const response = await fetch('/api/config');
    const config = await response.json();
    document.getElementById('currentConfig').textContent = JSON.stringify(config, null, 2);
}

async function addRule() {
    const pattern = document.getElementById('pattern').value;
    const action = document.getElementById('action').value;
    const proxy = document.getElementById('proxy').value;
    
    if (!pattern) {
        alert('Pattern is required');
        return;
    }
    
    const rule = {
        pattern,
        action,
        ...(proxy && { proxy })
    };
    
    await fetch('/api/rules', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(rule)
    });
    
    document.getElementById('pattern').value = '';
    document.getElementById('proxy').value = '';
    await loadRules();
    await loadConfig();
}

async function deleteRule(pattern) {
    await fetch(`/api/rules/${encodeURIComponent(pattern)}`, {
        method: 'DELETE'
    });
    await loadRules();
    await loadConfig();
}

// Load initial data
window.addEventListener('load', () => {
    loadRules();
    loadConfig();
});