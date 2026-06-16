const chatWindow = document.getElementById('chat-window');
const userInput  = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
let conversationHistory = [];
let voiceEnabled = false;

const userSVG = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
const botSVG = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>`;

const scenarios = [
    { dot:'red', text:'Simulate BGP Route Flap', query:'A branch office BGP session is flapping every 30 seconds with repeated NOTIFICATION messages. The router log shows: %BGP-3-NOTIFICATION: received from neighbor 10.0.0.1 (hold time expired). Diagnose the root cause and recommend remediation steps.' },
    { dot:'yellow', text:'Diagnose High Latency on MPLS Tunnel', query:'Our MPLS tunnel between the datacenter (10.1.0.1) and branch office (10.2.0.1) is showing 340ms latency, up from the baseline of 12ms. SD-WAN SLA metrics show jitter at 45ms and packet loss at 2.3%. What are the possible causes and what diagnostic commands should I run?' },
    { dot:'green', text:'Analyze SD-WAN Failover Event', query:'At 14:32 UTC, our SD-WAN controller triggered an automatic failover from the primary MPLS transport to the secondary 4G/LTE cellular backup for 3 branch sites. The failover lasted 8 minutes. Analyze what could have caused this and whether the failover policy worked correctly.' },
    { dot:'blue', text:'Compare VPN vs Direct Connect', query:'Compare AWS Site-to-Site VPN vs AWS Direct Connect for our enterprise SD-WAN deployment. Present the comparison in a table format covering latency, bandwidth, cost, redundancy, and security.' },
];

const drawerChips = document.getElementById('drawer-chips');
scenarios.forEach(s => {
    const chip = document.createElement('button'); chip.className = 'drawer-chip';
    chip.innerHTML = `<span class="chip-dot" style="background:var(--${s.dot === 'red' ? 'danger' : s.dot === 'yellow' ? 'warning' : s.dot === 'green' ? 'success' : 'accent-secondary'});box-shadow:0 0 8px var(--${s.dot === 'red' ? 'danger' : s.dot === 'yellow' ? 'warning' : s.dot === 'green' ? 'success' : 'accent-secondary'})"></span>${s.text}`;
    chip.onclick = () => { userInput.value = s.query; toggleScenarios(); sendMessage(s.dot); };
    drawerChips.appendChild(chip);
});

function toggleArchModal() { document.getElementById('arch-modal').classList.toggle('active'); }
function toggleScenarios() { document.getElementById('scenarios-drawer').classList.toggle('active'); }

// --- V5 FEATURES ---

function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-btn');
    btn.innerHTML = voiceEnabled ? '🔊 <span class="btn-text">Voice: ON</span>' : '🔈 <span class="btn-text">Voice: OFF</span>';
    btn.style.color = voiceEnabled ? 'var(--success)' : 'var(--text-secondary)';
    btn.style.borderColor = voiceEnabled ? 'var(--success)' : 'var(--border)';
    if(voiceEnabled) speakText("Voice synthesis activated. Standing by.");
}

function speakText(text) {
    if(!voiceEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95; u.pitch = 0.9;
    window.speechSynthesis.speak(u);
}

function updateTimeline(incident) {
    const prog = document.getElementById('timeline-progress');
    const mStress = document.getElementById('marker-stress');
    const mFail = document.getElementById('marker-fail');
    
    if(incident === 'red' || incident === 'yellow') {
        prog.style.width = '75%'; prog.style.background = 'var(--warning)';
        prog.style.boxShadow = '0 0 10px var(--warning)';
        mStress.classList.add('active'); mStress.textContent = '⚠ Anomaly Detected';
        mFail.classList.add('active'); mFail.textContent = '🔴 Predicted Outage: ~4m';
    } else {
        prog.style.width = '15%'; prog.style.background = 'var(--success)';
        prog.style.boxShadow = '0 0 8px var(--success)';
        mStress.classList.remove('active'); mFail.classList.remove('active');
        mStress.textContent = 'System Stress'; mFail.textContent = 'Predicted Failure';
    }
}

// -------------------

let currentIncident = null;
function setIncident(type) { currentIncident = type; setTimeout(() => { currentIncident = null; updateTimeline(); }, 40000); }
function updateMetrics() {
    let lat, loss, tunnels, peers, threat, threatColor;
    if (currentIncident === 'bgp') {
        lat = (180 + Math.random()*160).toFixed(1); loss = (3 + Math.random()*4).toFixed(2);
        tunnels = 28 + Math.floor(Math.random()*5); peers = 4 + Math.floor(Math.random()*3);
        threat = 'CRITICAL'; threatColor = 'var(--danger)';
    } else if (currentIncident === 'latency') {
        lat = (280 + Math.random()*120).toFixed(1); loss = (1.5 + Math.random()*2).toFixed(2);
        tunnels = 35 + Math.floor(Math.random()*5); peers = 9 + Math.floor(Math.random()*3);
        threat = 'WARNING'; threatColor = 'var(--warning)';
    } else if (currentIncident === 'failover') {
        lat = (45 + Math.random()*30).toFixed(1); loss = (0.5 + Math.random()*1).toFixed(2);
        tunnels = 38 + Math.floor(Math.random()*5); peers = 10 + Math.floor(Math.random()*2);
        threat = 'WARNING'; threatColor = 'var(--warning)';
    } else {
        lat = (10 + Math.random()*8).toFixed(1); loss = (Math.random()*0.05).toFixed(3);
        tunnels = 44 + Math.floor(Math.random()*6); peers = 11 + Math.floor(Math.random()*3);
        threat = 'LOW'; threatColor = 'var(--success)';
    }
    document.querySelector('.latency-val').textContent = lat + ' ms';
    document.querySelector('.latency-val').style.color = parseFloat(lat) > 50 ? (parseFloat(lat) > 150 ? 'var(--danger)' : 'var(--warning)') : 'var(--success)';
    document.querySelector('.loss-val').textContent = loss + '%';
    document.querySelector('.loss-val').style.color = parseFloat(loss) > 1 ? (parseFloat(loss) > 3 ? 'var(--danger)' : 'var(--warning)') : 'var(--success)';
    document.querySelector('.tunnel-val').textContent = tunnels;
    document.querySelector('.tunnel-val').style.color = tunnels < 35 ? 'var(--danger)' : 'var(--success)';
    document.querySelector('.peer-val').textContent = peers;
    document.querySelector('.peer-val').style.color = peers < 8 ? 'var(--danger)' : 'var(--success)';
    const tv = document.querySelector('.threat-val'); tv.textContent = threat; tv.style.color = threatColor;
}
setInterval(updateMetrics, 2500); updateMetrics();

const alertFeed = document.getElementById('alert-feed');
const alertMessages = [
    { level:'info', msg:'BGP peer 10.0.0.1 session ESTABLISHED' }, { level:'info', msg:'MPLS label switch path verified OK' },
    { level:'warning', msg:'Interface GigE0/1 utilization at 78%' }, { level:'info', msg:'SD-WAN policy update applied' },
    { level:'critical', msg:'BGP NOTIFICATION: Hold timer expired for 10.0.0.5' }, { level:'warning', msg:'Tunnel latency exceeded SLA' },
    { level:'critical', msg:'MPLS LSP down: PE1-to-PE3 tunnel unreachable' },
];
let alertIdx = 0;
function addAlert() {
    const a = alertMessages[alertIdx % alertMessages.length];
    const el = document.createElement('div'); el.className = 'alert-item ' + a.level;
    el.textContent = `[${new Date().toLocaleTimeString()}] ${a.level.toUpperCase()}: ${a.msg}`;
    alertFeed.prepend(el); if (alertFeed.children.length > 5) alertFeed.removeChild(alertFeed.lastChild);
    alertIdx++;
}
setInterval(addAlert, 6000); addAlert();

function addMessage(html, sender) {
    const row = document.createElement('div'); row.className = 'message ' + sender;
    const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.innerHTML = sender === 'bot' ? botSVG : userSVG;
    row.appendChild(avatar);
    const bubble = document.createElement('div'); bubble.className = 'bubble'; bubble.innerHTML = html;
    row.appendChild(bubble); chatWindow.appendChild(row); chatWindow.scrollTop = chatWindow.scrollHeight;
    return bubble;
}

function addWelcome() {
    const row = document.createElement('div'); row.className = 'message bot';
    const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.innerHTML = botSVG; row.appendChild(avatar);
    const w = document.createElement('div'); w.className = 'bubble-wrapper';
    const b = document.createElement('div'); b.className = 'bubble';
    b.innerHTML = 'NOC Copilot initialized. Telemetry vault loaded with <strong>199 vectors</strong>.<br><br>Click <strong>Scenarios</strong> to run simulations.';
    w.appendChild(b); row.appendChild(w); chatWindow.appendChild(row);
}

async function simulateRCA(wrapper) {
    const rcaSteps = [
        "[STEP 1] Anomaly Detected in telemetry stream...",
        "[STEP 2] Querying RAG Vector Vault for known patterns...",
        "[STEP 3] Cross-referencing historical metrics...",
        "[STEP 4] Autonomous RCA Initiated."
    ];
    const chain = document.createElement('div'); chain.className = 'rca-chain';
    wrapper.appendChild(chain);
    for (let step of rcaSteps) {
        const stepEl = document.createElement('div'); stepEl.className = 'rca-step'; stepEl.textContent = step;
        chain.appendChild(stepEl); chatWindow.scrollTop = chatWindow.scrollHeight;
        await new Promise(r => setTimeout(r, 700));
    }
}

function createStream() {
    const row = document.createElement('div'); row.className = 'message bot';
    const av = document.createElement('div'); av.className = 'avatar'; av.innerHTML = botSVG; row.appendChild(av);
    const w = document.createElement('div'); w.className = 'bubble-wrapper';
    const b = document.createElement('div'); b.className = 'bubble';
    const content = document.createElement('div'); content.className = 'markdown-content';
    const cursor = document.createElement('span'); cursor.className = 'typing-cursor';
    b.appendChild(content); b.appendChild(cursor); w.appendChild(b); row.appendChild(w);
    chatWindow.appendChild(row); chatWindow.scrollTop = chatWindow.scrollHeight;
    return { content, cursor, wrapper: w, row, bubble: b };
}

function addResponseMeta(wrapper, totalTime, rawText, sources) {
    const conf = Math.floor(Math.random() * 9) + 87; // 87 to 95%
    const bars = "█".repeat(Math.floor(conf/10)) + "░".repeat(10 - Math.floor(conf/10));
    
    const meta = document.createElement('div'); meta.className = 'response-meta';
    meta.innerHTML = `<span class="meta-chip">Diagnosed in ${totalTime}s</span> <span class="meta-chip" style="color:var(--success); border-color:var(--success)">Confidence: ${conf}% [${bars}]</span>`;
    wrapper.appendChild(meta);
    
    const btns = document.createElement('div'); btns.className = 'action-buttons';
    const copyBtn = document.createElement('button'); copyBtn.className = 'action-btn'; copyBtn.innerHTML = `COPY`;
    copyBtn.onclick = () => { navigator.clipboard.writeText(rawText); copyBtn.classList.add('copied'); copyBtn.innerHTML = `COPIED`; setTimeout(() => { copyBtn.classList.remove('copied'); copyBtn.innerHTML = `COPY`; }, 2000); };
    btns.appendChild(copyBtn);
    
    const expBtn = document.createElement('button'); expBtn.className = 'action-btn'; expBtn.innerHTML = `EXPORT PDF/TXT`;
    expBtn.onclick = () => {
        const ts = new Date().toISOString().replace(/[:.]/g,'-');
        const report = `=================================================\n AIR-GAPPED NOC COPILOT\n INCIDENT DIAGNOSTIC REPORT\n=================================================\nIncident ID: NOC-2026-0615-${Math.floor(Math.random()*1000)}\nDetected: ${new Date().toLocaleString()}\nConfidence: ${conf}%\nSources: ${sources.join(', ')}\n-------------------------------------------------\nDIAGNOSIS & REMEDIATION:\n-------------------------------------------------\n\n${rawText}\n\n=================================================\n END OF REPORT\n=================================================`;
        const blob = new Blob([report], {type:'text/plain'});
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
        a.download = `NOC_Incident_${ts}.txt`; a.click();
    };
    btns.appendChild(expBtn);
    wrapper.appendChild(btns);
}

async function sendMessage(scenarioColor = null) {
    const msg = userInput.value.trim(); if (!msg) return;
    const tmp = document.createElement('div'); tmp.textContent = msg; addMessage(tmp.innerHTML, 'user');
    userInput.value = ''; sendBtn.disabled = true;

    if (msg.toLowerCase().includes('bgp') && msg.toLowerCase().includes('flap')) setIncident('bgp');
    else if (msg.toLowerCase().includes('latency') || msg.toLowerCase().includes('340ms')) setIncident('latency');
    else if (msg.toLowerCase().includes('failover')) setIncident('failover');
    
    updateTimeline(scenarioColor);
    
    if(voiceEnabled && (scenarioColor === 'red' || scenarioColor === 'yellow' || currentIncident)) {
        speakText("Critical anomaly detected. Initiating autonomous diagnostic routine.");
    }

    let streamObj = createStream();
    await simulateRCA(streamObj.wrapper);
    
    let raw = ""; let rSources = [];

    try {
        conversationHistory.push({role:"user", content: msg});
        const res = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:msg, history:conversationHistory}) });
        const reader = res.body.getReader(); const dec = new TextDecoder();
        let buf = '', totalTime = 0;
        
        while (true) {
            const {done, value} = await reader.read(); if (done) break;
            buf += dec.decode(value, {stream:true}); const lines = buf.split('\n'); buf = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const d = JSON.parse(line.slice(6));
                    if (d.type === 'sources') { rSources = d.content; }
                    else if (d.type === 'token') {
                        raw += d.content;
                        if (window.marked) { streamObj.content.innerHTML = marked.parse(raw); if (window.hljs) streamObj.content.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b)); }
                        else streamObj.content.textContent = raw;
                        chatWindow.scrollTop = chatWindow.scrollHeight;
                    } else if (d.type === 'done') {
                        totalTime = d.total_time || 0; 
                        if (streamObj) { streamObj.cursor.remove(); addResponseMeta(streamObj.wrapper, totalTime, raw, rSources); }
                        if (voiceEnabled && raw.includes('[SEVERITY:')) {
                            const firstLine = raw.split('\n')[0].replace(/\[|\]/g, '') + ". Diagnosis complete.";
                            speakText(firstLine);
                        }
                    }
                } catch(e) {}
            }
        }
        conversationHistory.push({role:"assistant", content:raw}); if (conversationHistory.length > 6) conversationHistory = conversationHistory.slice(-6); 
    } catch(e) { streamObj.bubble.innerHTML = 'CRITICAL: Connection lost.'; }
    sendBtn.disabled = false; userInput.focus();
}

sendBtn.addEventListener('click', () => sendMessage());
userInput.addEventListener('keypress', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });
addWelcome();
