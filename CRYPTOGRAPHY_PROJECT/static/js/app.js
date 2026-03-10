/* global bootstrap, Chart */
const API_SCAN='/api/scan';
const API_LOGS='/api/logs';
const API_CLEAR='/api/clear_logs';

let charts={risk:null,enc:null};
let lastAlert=0;
let connectedOnly=false;

function qs(sel){return document.querySelector(sel);} 
function qsa(sel){return Array.from(document.querySelectorAll(sel));}

function riskBadge(score){
  if(score<30) return '<span class="badge bg-success">Safe</span>';
  if(score<60) return '<span class="badge bg-warning text-dark">Suspicious</span>';
  return '<span class="badge bg-danger">Dangerous</span>';
}

function alertPopup(title,body){
  const box=qs('#alerts');
  const el=document.createElement('div');
  el.className='alert alert-danger alert-dismissible fade show alert-pop';
  el.innerHTML=`<div class="d-flex align-items-start"><i class="bi bi-exclamation-octagon-fill me-2 fs-4"></i><div><div class="fw-bold">${title}</div><div class="small">${body}</div></div></div><button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  box.appendChild(el);
  setTimeout(()=>{try{bootstrap.Alert.getOrCreateInstance(el).close();}catch(_){}} ,5500);
}

function groupBySSID(arr){const m={};arr.forEach(n=>{const k=n.ssid&&n.ssid.length?n.ssid:'<hidden>';(m[k]=m[k]||[]).push(n);});return m;}

function ensureCharts(){
  const rc=qs('#chart-risk'); const ec=qs('#chart-enc');
  if(rc && !charts.risk){ charts.risk=new Chart(rc,{type:'bar',data:{labels:['Safe','Suspicious','Dangerous'],datasets:[{data:[0,0,0],backgroundColor:['#198754','#ffc107','#dc3545']}]},options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#bfe'}},y:{ticks:{color:'#bfe'}}}}}); }
  if(ec && !charts.enc){ charts.enc=new Chart(ec,{type:'doughnut',data:{labels:['OPEN','WEP','WPA','WPA2','WPA3'],datasets:[{data:[0,0,0,0,0],backgroundColor:['#dc3545','#ff6b6b','#0dcaf0','#198754','#20c997']} ]},options:{plugins:{legend:{labels:{color:'#bfe'}}}}}); }
}

function updateCharts(nets){ ensureCharts(); if(charts.risk){ const a=nets.filter(n=>n.risk<30).length; const b=nets.filter(n=>n.risk>=30 && n.risk<60).length; const c=nets.filter(n=>n.risk>=60).length; charts.risk.data.datasets[0].data=[a,b,c]; charts.risk.update('none'); } if(charts.enc){ const cts={OPEN:0,WEP:0,WPA:0,WPA2:0,WPA3:0}; nets.forEach(n=>cts[n.encryption]=(cts[n.encryption]||0)+1); charts.enc.data.datasets[0].data=[cts.OPEN||0,cts.WEP||0,cts.WPA||0,cts.WPA2||0,cts.WPA3||0]; charts.enc.update('none'); } }

function updateRadar(nets){ const r=qs('#radar'); if(!r) return; qsa('.radar .radar-node').forEach(n=>n.remove()); const R=r.clientWidth/2-14; nets.slice(0,24).forEach((n,i)=>{ const angle=(i/24)*2*Math.PI+(Date.now()/1000)% (2*Math.PI); const d=Math.max(20,R*(0.3+Math.random()*0.6)); const x=Math.cos(angle)*d; const y=Math.sin(angle)*d; const el=document.createElement('div'); el.className='radar-node'; el.style.left=`calc(50% + ${x}px)`; el.style.top=`calc(50% + ${y}px)`; el.title=`${n.ssid||'<hidden>'} | ${n.bssid} | ${n.signal} dBm`; r.appendChild(el); }); }

function updateMetrics(nets){ const t=qs('#metric-total'); const s=qs('#metric-suspicious'); if(t) t.textContent=String(nets.length); if(s) s.textContent=String(nets.filter(n=>n.risk>=30).length); }

function renderTable(nets){ const tb=qs('#table-scanner tbody'); if(!tb) return; tb.innerHTML=''; const by=groupBySSID(nets); nets.sort((a,b)=>b.signal-a.signal).forEach(n=>{ const tr=document.createElement('tr'); const evil=(by[(n.ssid||'<hidden>')].length>1); const weak=(n.encryption==='OPEN'||n.encryption==='WEP'); if(evil) tr.classList.add('tr-evil'); if(weak) tr.classList.add('tr-weak'); const alerts=[]; if(evil) alerts.push('<span class="text-danger fw-bold">Evil Twin</span>'); if(weak) alerts.push('<span class="text-warning">Weak</span>'); if(n.unknown_mac) alerts.push('<span class="text-info">Unknown MAC</span>'); if(n.signal>=-40) alerts.push('<span class="text-danger">Very Strong</span>'); tr.innerHTML=`<td>${n.ssid||'<hidden>'}</td><td class="small">${n.bssid}</td><td>${n.signal} dBm</td><td>${n.channel||'-'}</td><td>${n.encryption}</td><td>${riskBadge(n.risk)}</td><td>${alerts.join(' • ')}</td>`; tb.appendChild(tr); }); }

function updateAnalysis(nets){ const c=qs('#analysis-cards'); if(!c) return; c.innerHTML=''; const by=groupBySSID(nets); nets.sort((a,b)=>b.risk-a.risk).forEach(n=>{ const evil=(by[(n.ssid||'<hidden>')].length>1); const bar= n.risk<30?'bg-success':(n.risk<60?'bg-warning':'bg-danger'); const d=document.createElement('div'); d.className='col-12 col-md-6 col-xl-4'; d.innerHTML=`<div class="panel panel-neon h-100"><div class="panel-body"><div class="d-flex justify-content-between align-items-center"><div class="fw-bold">${n.ssid||'<hidden>'}</div><span>${riskBadge(n.risk)}</span></div><div class="text-muted small">${n.bssid}</div><div class="mt-2 small d-flex justify-content-between"><span>Encryption: <span class="text-info">${n.encryption}</span></span><span>Signal: <span class="text-info">${n.signal} dBm</span></span></div><div class="progress progress-risk mt-2"><div class="progress-bar ${bar}" style="width:${n.risk}%"></div></div><div class="mt-2 small">${evil?'<span class="text-danger fw-bold">Possible Evil Twin Attack Detected</span><br/>':''}${n.encryption==='OPEN'?'Recommendation: Avoid connecting and use VPN.':''}${n.encryption==='WEP'?'Recommendation: Treat as insecure; prefer WPA2/WPA3.':''}</div></div></div>`; c.appendChild(d); }); }

function maybeAlerts(nets){ const now=Date.now(); if(now-lastAlert<5000) return; const evil=nets.find(n=>n.evil_twin); if(evil){ alertPopup('Warning: Possible Fake WiFi Network Detected', `${evil.ssid||'<hidden>'} appears with multiple BSSIDs.`); lastAlert=now; return; } const dang=nets.find(n=>n.risk>=60); if(dang){ alertPopup('Dangerous Network Detected', `${dang.ssid||'<hidden>'} • ${dang.encryption} • ${dang.signal} dBm`); lastAlert=now; } }

async function refresh(){ try{ const url=API_SCAN+(connectedOnly?'?connected_only=1':''); const data=await (await fetch(url)).json(); const nets=data.networks||[]; updateRadar(nets); updateMetrics(nets); renderTable(nets); updateCharts(nets); updateAnalysis(nets); maybeAlerts(nets);}catch(e){console.error(e);} }

function setup(){ const toggle=qs('#toggle-connected-only'); if(toggle){ toggle.addEventListener('change',()=>{ connectedOnly=toggle.checked; refresh(); }); }
  refresh(); setInterval(refresh,5000);
  // Logs
  const tbody=qs('#table-logs tbody'); if(tbody){ async function loadLogs(){ try{ const d=await (await fetch(API_LOGS)).json(); tbody.innerHTML=''; (d.logs||[]).slice().reverse().forEach(l=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td class="small">${l.timestamp}</td><td>${l.ssid}</td><td class="small">${l.bssid}</td><td>${l.attack_type}</td><td>${l.risk}</td>`; tbody.appendChild(tr);}); }catch(e){console.error(e);} } loadLogs(); setInterval(loadLogs,5000); const clr=qs('#btn-clear-logs'); if(clr){ clr.addEventListener('click', async ()=>{ try{ await fetch(API_CLEAR,{method:'POST'}); }catch(e){} }); } }
}

document.addEventListener('DOMContentLoaded', setup);
