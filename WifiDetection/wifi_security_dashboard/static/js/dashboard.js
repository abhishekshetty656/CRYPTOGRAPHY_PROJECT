/* global io, Chart */
let socket;
let signalHistory = {}; // {bssid: [{t, v}]}
let charts = {};

function el(id){return document.getElementById(id)}

function formatRisk(risk){
  const map = {LOW: 'bg-emerald-500/20 text-emerald-300', MEDIUM: 'bg-amber-500/20 text-amber-300', HIGH: 'bg-rose-500/20 text-rose-300'};
  return map[risk] || 'bg-slate-600 text-slate-200';
}

function updateCards(payload){
  const total = payload.networks.length;
  const suspicious = payload.suspicious.length;
  el('card-total').innerText = total;
  el('card-suspicious').innerText = suspicious;
  const cur = payload.current || {}; 
  el('card-connected').innerText = cur.connected_ssid || 'Not connected';
  const eth = payload.ethernet || {interfaces: []};
  el('card-ethernet').innerText = eth.interfaces.some(i=>i.status==='up') ? 'Connected' : 'Disconnected';
  const net = payload.internet || {online:false};
  el('card-internet').innerText = net.online ? 'Online' : 'Offline';
  el('card-internet').className = 'text-xl font-semibold ' + (net.online ? 'text-emerald-300' : 'text-rose-300');
  el('card-internet-detail').innerText = net.online ? `${net.target} • ${net.latency_ms} ms` : '';
}

function renderTable(networks, suspicious){
  const riskBySSID = {};
  suspicious.forEach(s=>{riskBySSID[s.ssid]=s.risk});
  const tbody = el('networks-body');
  tbody.innerHTML = '';
  for(const n of networks){
    const tr = document.createElement('tr');
    tr.className = 'border-b border-slate-700 hover:bg-slate-800/60';
    const risk = riskBySSID[n.ssid] || 'LOW';
    tr.innerHTML = `
      <td class="px-3 py-2">${n.ssid || '(hidden)'}<div class="text-xs text-slate-400">${n.frequency || ''}</div></td>
      <td class="px-3 py-2 font-mono text-xs">${n.bssid || ''}</td>
      <td class="px-3 py-2">${n.signal ?? ''}%</td>
      <td class="px-3 py-2">${n.channel ?? ''}</td>
      <td class="px-3 py-2">${n.security || ''}<div class="text-xs text-slate-400">${n.encryption || ''}</div></td>
      <td class="px-3 py-2">${n.vendor || ''}</td>
      <td class="px-3 py-2"><span class="px-2 py-1 rounded ${formatRisk(risk)}">${risk}</span></td>
    `;
    tbody.appendChild(tr);
  }
}

function ensureChart(ctx, type, cfg){
  if(charts[ctx.canvas.id]) return charts[ctx.canvas.id];
  const c = new Chart(ctx, {type, data: cfg.data, options: cfg.options});
  charts[ctx.canvas.id] = c;
  return c;
}

function updateCharts(payload){
  const now = Date.parse(payload.timestamp);
  for(const n of payload.networks){
    if(!n.bssid) continue;
    if(!signalHistory[n.bssid]) signalHistory[n.bssid] = [];
    signalHistory[n.bssid].push({t: now, v: n.signal || 0, ssid: n.ssid || '(hidden)'});
    if(signalHistory[n.bssid].length > 60) signalHistory[n.bssid].shift();
  }
  // Signal history of top 5 by strength now
  const top = [...payload.networks].filter(n=>n.signal!=null).sort((a,b)=>b.signal-a.signal).slice(0,5);
  const labels = (signalHistory[top[0]?.bssid]||[]).map(p=>new Date(p.t).toLocaleTimeString());
  const datasets = top.map((n,i)=>({
    label: `${n.ssid||'(hidden)'} ${n.bssid.slice(-5)}`,
    data: (signalHistory[n.bssid]||[]).map(p=>p.v),
    borderColor: ['#60a5fa','#a78bfa','#34d399','#f472b6','#f59e0b'][i%5],
    tension: .3
  }));
  const ctx1 = document.getElementById('chart-signal').getContext('2d');
  const ch1 = ensureChart(ctx1, 'line', {
    data: { labels, datasets },
    options: {responsive:true, plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}, suggestedMin:0, suggestedMax:100}}}
  });
  ch1.data.labels = labels; ch1.data.datasets = datasets; ch1.update();

  // Channel usage
  const chan = payload.channel_stats || {channels:[], counts:[]};
  const ctx2 = document.getElementById('chart-channels').getContext('2d');
  const ch2 = ensureChart(ctx2, 'bar', {
    data: { labels: chan.channels, datasets: [{ label: 'Networks', data: chan.counts, backgroundColor:'#38bdf8'}]},
    options: {plugins:{legend:{labels:{color:'#cbd5e1'}}}, scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}, beginAtZero:true}}}
  });
  ch2.data.labels = chan.channels; ch2.data.datasets[0].data = chan.counts; ch2.update();

  // Security distribution
  const secCounts = {};
  for(const n of payload.networks){
    const key = (n.security||'Open').split('+')[0];
    secCounts[key] = (secCounts[key]||0)+1;
  }
  const secLabels = Object.keys(secCounts);
  const secData = Object.values(secCounts);
  const ctx3 = document.getElementById('chart-security').getContext('2d');
  const ch3 = ensureChart(ctx3, 'doughnut', {
    data: { labels: secLabels, datasets: [{ data: secData, backgroundColor:['#22d3ee','#a78bfa','#60a5fa','#34d399','#f97316','#ef4444'] }]},
    options: {plugins:{legend:{labels:{color:'#cbd5e1'}}}}
  });
  ch3.data.labels = secLabels; ch3.data.datasets[0].data = secData; ch3.update();
}

function renderAlerts(suspicious){
  const box = el('alerts');
  box.innerHTML = '';
  for(const s of suspicious){
    const div = document.createElement('div');
    const color = s.risk==='HIGH'?'border-rose-500/50 bg-rose-500/10':(s.risk==='MEDIUM'?'border-amber-500/50 bg-amber-500/10':'border-emerald-500/50 bg-emerald-500/10');
    div.className = `border ${color} rounded p-3 mb-2`;
    div.innerHTML = `<div class="text-slate-200 font-semibold">Evil Twin suspicion: ${s.ssid}</div>
      <div class="text-slate-400 text-sm">BSSIDs: ${s.bssids.join(', ')} | Duplicates: ${s.count} | Open var: ${s.has_open_variant?'Yes':'No'} | Risk: ${s.risk}</div>`;
    box.appendChild(div);
  }
  if(suspicious.length===0){
    box.innerHTML = '<div class="text-slate-400">No alerts.</div>';
  }
}

function connectSocket(){
  socket = io();
  socket.on('connect', ()=>{
    // request initial via REST in case
    fetch('/api/networks').then(r=>r.json()).then(()=>{}).catch(()=>{});
  });
  socket.on('scan_update', payload=>{
    updateCards(payload);
    renderTable(payload.networks, payload.suspicious);
    updateCharts(payload);
    renderAlerts(payload.suspicious);
  });
  socket.on('scan_error', err=>{
    console.error('Scan error', err);
  });
}

window.addEventListener('DOMContentLoaded', ()=>{
  connectSocket();
});
