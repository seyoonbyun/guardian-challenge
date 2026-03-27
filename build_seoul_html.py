import os

b64_path = os.path.join(os.path.dirname(__file__), 'seoul3_b64_clean.txt')
out_path = os.path.join(os.path.dirname(__file__), 'seoul-map-preview.html')

with open(b64_path, 'r') as f:
    b64 = f.read().strip().replace('\r','').replace('\n','')

part1 = r'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GUARDIAN - Seoul Detailed Map</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0a;color:#fff;overflow:hidden;height:100vh;width:100vw;}

/* TOP BAR */
.topbar{height:46px;background:#111;border-bottom:1px solid #222;display:flex;align-items:center;justify-content:space-between;padding:0 20px;z-index:100;position:relative;}
.topbar .brand{display:flex;align-items:center;gap:10px;}
.topbar .brand .icon{width:26px;height:26px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;color:#fff;}
.topbar .brand span{font-weight:700;font-size:14px;letter-spacing:4px;color:#c41a2e;}
.topbar nav{display:flex;gap:4px;position:absolute;left:50%;transform:translateX(-50%);}
.topbar nav a{color:#555;text-decoration:none;font-size:10px;font-weight:600;letter-spacing:1.5px;padding:5px 12px;border-radius:3px;text-transform:uppercase;transition:all .2s;}
.topbar nav a:hover{color:#999;}
.topbar nav a.active{color:#ccc;background:rgba(255,255,255,0.05);}
.topbar .clock{color:#555;font-size:11px;font-weight:500;letter-spacing:0.5px;}

/* MAIN LAYOUT */
.main{display:flex;height:calc(100vh - 46px);}

/* LEFT SIDEBAR */
.sidebar-left{width:220px;background:#111;border-right:1px solid #1a1a1a;display:flex;flex-direction:column;overflow:hidden;}
.profile-card{padding:14px 16px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;gap:10px;}
.profile-avatar{width:32px;height:32px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;}
.profile-info{display:flex;flex-direction:column;}
.profile-name{font-size:12px;font-weight:700;color:#eee;letter-spacing:0.5px;}
.profile-sub{font-size:9px;color:#555;letter-spacing:0.5px;margin-top:1px;}

/* TABS */
.tabs{display:flex;border-bottom:1px solid #1a1a1a;}
.tab-btn{flex:1;padding:9px 0;text-align:center;font-size:9px;font-weight:700;letter-spacing:1.5px;color:#555;background:transparent;border:none;cursor:pointer;text-transform:uppercase;transition:all .2s;border-bottom:2px solid transparent;}
.tab-btn.active{color:#ccc;border-bottom-color:#c41a2e;background:rgba(196,26,46,0.05);}
.tab-btn:hover{color:#888;}

.section-header{padding:12px 16px 8px;font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;}
.region-list{flex:1;overflow-y:auto;padding:0 8px 8px;}
.region-list::-webkit-scrollbar{width:3px;}
.region-list::-webkit-scrollbar-track{background:transparent;}
.region-list::-webkit-scrollbar-thumb{background:#333;border-radius:2px;}

.region-item{display:flex;align-items:center;padding:7px 10px;margin-bottom:1px;border-radius:4px;cursor:pointer;transition:all .15s;border-left:2px solid transparent;gap:8px;}
.region-item:hover{background:rgba(255,255,255,0.03);}
.region-item.active{background:rgba(196,26,46,0.08);border-left-color:#c41a2e;}
.region-dot{width:6px;height:6px;background:#c41a2e;border-radius:50%;flex-shrink:0;}
.region-name{flex:1;font-size:12px;color:#bbb;font-weight:500;}
.region-item.active .region-name{color:#fff;}
.region-count{font-size:10px;color:#666;font-weight:600;background:#1a1a1a;padding:1px 7px;border-radius:8px;min-width:24px;text-align:center;}
.region-item.active .region-count{background:rgba(196,26,46,0.2);color:#e88;}

.back-btn{margin:10px 12px;padding:10px;background:#333;color:#ccc;border:none;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:2px;cursor:pointer;text-transform:uppercase;transition:all .2s;text-align:center;}
.back-btn:hover{background:#444;}
.deploy-btn{margin:0 12px 10px;padding:10px;background:#c41a2e;color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:2px;cursor:pointer;text-transform:uppercase;transition:all .2s;}
.deploy-btn:hover{background:#d42a3e;}

/* CENTER MAP */
.map-center{flex:1;display:flex;flex-direction:column;position:relative;background:#0a0a0a;}
.map-area{flex:1;position:relative;overflow:hidden;}
.dot-grid{position:absolute;inset:0;background-image:radial-gradient(circle,#1a1a1a 1px,transparent 1px);background-size:24px 24px;opacity:0.5;}
.map-container{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#0a0a0a;}
.map-container canvas{user-select:none;pointer-events:none;}

/* Marker overlay */
#markerOverlay{position:absolute;pointer-events:none;}
@keyframes pulse{0%,100%{box-shadow:0 0 6px rgba(196,26,46,0.5);}50%{box-shadow:0 0 16px rgba(196,26,46,0.9);}}

/* Zoom controls */
.zoom-controls{position:absolute;left:14px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:2px;z-index:20;}
.zoom-btn{width:28px;height:28px;background:#1a1a1a;border:1px solid #333;color:#888;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;transition:all .2s;}
.zoom-btn:first-child{border-radius:4px 4px 0 0;}
.zoom-btn:last-child{border-radius:0 0 4px 4px;}
.zoom-btn:hover{background:#252525;color:#ccc;}

/* Bottom stats */
.bottom-stats{height:60px;display:flex;align-items:center;justify-content:center;gap:60px;border-top:1px solid #1a1a1a;background:#0d0d0d;}
.stat-big{display:flex;flex-direction:column;align-items:center;}
.stat-big .val{font-size:28px;font-weight:800;color:#fff;letter-spacing:1px;}
.stat-big .label{font-size:8px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;}

/* RIGHT PANEL */
.sidebar-right{width:300px;background:#111;border-left:1px solid #1a1a1a;display:flex;flex-direction:column;overflow-y:auto;}
.sidebar-right::-webkit-scrollbar{width:3px;}
.sidebar-right::-webkit-scrollbar-track{background:transparent;}
.sidebar-right::-webkit-scrollbar-thumb{background:#333;border-radius:2px;}

.right-header{padding:16px 20px 6px;font-size:9px;font-weight:600;letter-spacing:2px;color:#444;text-transform:uppercase;}
.right-region-name{padding:0 20px;font-size:26px;font-weight:800;color:#fff;letter-spacing:1px;}
.right-big-number{padding:12px 20px 0;display:flex;align-items:baseline;gap:10px;}
.right-big-number .num{font-size:42px;font-weight:800;color:#c41a2e;}
.right-big-number .badge{font-size:11px;font-weight:700;color:#4caf50;background:rgba(76,175,80,0.1);padding:3px 8px;border-radius:10px;}
.right-label{padding:2px 20px 0;font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;}

.quota-section{padding:16px 20px 0;}
.quota-title{font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;margin-bottom:8px;}
.quota-bar-bg{height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden;}
.quota-bar-fill{height:100%;background:#c41a2e;border-radius:3px;transition:width .5s;}
.quota-pct{font-size:11px;color:#888;margin-top:4px;text-align:right;font-weight:600;}

.chapters-section{padding:16px 20px 0;}
.chapters-title{font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;margin-bottom:10px;}
.chapter-item{display:flex;align-items:center;margin-bottom:8px;gap:8px;}
.chapter-name{width:50px;font-size:11px;color:#999;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chapter-bar-bg{flex:1;height:8px;background:#1a1a1a;border-radius:2px;overflow:hidden;}
.chapter-bar-fill{height:100%;background:#c41a2e;border-radius:2px;transition:width .5s;}
.chapter-count{font-size:10px;color:#666;font-weight:600;width:24px;text-align:right;flex-shrink:0;}

.spotlight-section{margin-top:auto;padding:14px 20px;border-top:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between;}
.spotlight-label{font-size:8px;color:#444;letter-spacing:1.5px;text-transform:uppercase;}
.spotlight-name{font-size:12px;color:#ccc;font-weight:600;margin-top:2px;}
.spotlight-avatar{width:32px;height:32px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;}

/* Scan line */
.scan-line{position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(196,26,46,0.15),transparent);animation:scanMove 6s linear infinite;z-index:5;pointer-events:none;}
@keyframes scanMove{0%{top:0;}100%{top:100%;}}

/* Marker labels */
.marker-group{position:absolute;transform:translate(-50%,-50%);cursor:pointer;z-index:10;pointer-events:auto;display:flex;flex-direction:column;align-items:center;}
.marker-group .dot{width:8px;height:8px;background:#c41a2e;border-radius:50%;box-shadow:0 0 6px rgba(196,26,46,0.5);transition:all .2s;}
.marker-group:hover .dot{transform:scale(1.4);box-shadow:0 0 12px rgba(196,26,46,0.8);}
.marker-group.active .dot{animation:pulse 1.5s ease-in-out infinite;}
.marker-group .label{margin-top:3px;font-size:9px;font-weight:700;color:#999;letter-spacing:0.5px;white-space:nowrap;text-shadow:0 1px 3px rgba(0,0,0,0.8);}
.marker-group.active .label{color:#fff;}
.marker-group .count{font-size:10px;font-weight:800;color:#c41a2e;text-shadow:0 1px 3px rgba(0,0,0,0.8);}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
  <div class="brand">
    <div class="icon">G</div>
    <span>GUARDIAN</span>
  </div>
  <nav>
    <a href="#">REGIONAL</a>
    <a href="#">DIAGNOSTICS</a>
    <a href="#" class="active">SEOUL MAP</a>
    <a href="#">SETTINGS</a>
  </nav>
  <div class="clock" id="clock"></div>
</div>

<!-- MAIN -->
<div class="main">

  <!-- LEFT SIDEBAR -->
  <div class="sidebar-left">
    <div class="profile-card">
      <div class="profile-avatar">P</div>
      <div class="profile-info">
        <div class="profile-name">Protocol Alpha</div>
        <div class="profile-sub">Seoul Command v2.0</div>
      </div>
    </div>
    <div class="tabs">
      <button class="tab-btn active" id="tabDistrict">DISTRICT</button>
      <button class="tab-btn" id="tabAll">ALL</button>
    </div>
    <div class="section-header">SEOUL DISTRICTS</div>
    <div class="region-list" id="regionList"></div>
    <a class="back-btn" href="map-preview.html">&larr; NATIONAL MAP</a>
    <button class="deploy-btn">DEPLOY MONITOR</button>
  </div>

  <!-- CENTER MAP -->
  <div class="map-center">
    <div class="map-area">
      <div class="dot-grid"></div>
      <div class="scan-line"></div>
      <div class="map-container" id="mapContainer">
        <img src="data:image/jpeg;base64,'''

part2 = r'''" id="mapImg" style="display:none" />
        <canvas id="mapCanvas"></canvas>
      </div>
      <div id="markerOverlay"></div>
      <div class="zoom-controls">
        <div class="zoom-btn" onclick="zoomIn()">+</div>
        <div class="zoom-btn" onclick="zoomOut()">&minus;</div>
      </div>
    </div>
    <div class="bottom-stats">
      <div class="stat-big">
        <div class="val" id="totalCount">0</div>
        <div class="label">SEOUL GUARDIANS</div>
      </div>
      <div class="stat-big">
        <div class="val" id="activeRate">0%</div>
        <div class="label">ACTIVE RATE</div>
      </div>
    </div>
  </div>

  <!-- RIGHT PANEL -->
  <div class="sidebar-right">
    <div class="right-header">SELECTED DISTRICT</div>
    <div class="right-region-name" id="rightRegionName">GANGNAM</div>
    <div class="right-big-number">
      <div class="num" id="rightCount">0</div>
      <div class="badge" id="rightBadge">+0%</div>
    </div>
    <div class="right-label">GUARDIANS IN DISTRICT</div>

    <div class="quota-section">
      <div class="quota-title">QUOTA FULFILLMENT</div>
      <div class="quota-bar-bg"><div class="quota-bar-fill" id="quotaBar" style="width:0%"></div></div>
      <div class="quota-pct" id="quotaPct">0%</div>
    </div>

    <div class="chapters-section">
      <div class="chapters-title">TOP 5 CHAPTERS</div>
      <div id="chaptersList"></div>
    </div>

    <div class="spotlight-section">
      <div>
        <div class="spotlight-label">DISTRICT MVP SPOTLIGHT</div>
        <div class="spotlight-name" id="spotlightName">-</div>
      </div>
      <div class="spotlight-avatar" id="spotlightAvatar">-</div>
    </div>
  </div>

</div>

<script>
const API_URL = 'https://script.google.com/macros/s/AKfycbyXXPPtJ-5T98hc63xxfLXtKqfvTK3YaUkxTyNjEbNofiWyAGf7N2GT6i4k1X2xDKUXEw/exec?action=getData';

// Seoul district positions (% on seoul3.jpg)
const DISTRICT_POSITIONS = {
  '\uac15\ub0a8': {x:60,y:72},
  '\uc11c\ucd08': {x:48,y:78},
  '\uc131\ub3d9': {x:58,y:50},
  '\ub9c8\ud3ec': {x:32,y:48},
  '\uc1a1\ud30c': {x:78,y:68},
  '\uc911\uad6c': {x:48,y:50},
  '\uc601\ub4f1\ud3ec': {x:30,y:64}
};

const EN_NAMES = {
  '\uac15\ub0a8':'GANGNAM','\uc11c\ucd08':'SEOCHO','\uc131\ub3d9':'SEONGDONG',
  '\ub9c8\ud3ec':'MAPO','\uc1a1\ud30c':'SONGPA','\uc911\uad6c':'JUNGGU',
  '\uc601\ub4f1\ud3ec':'YEONGDEUNGPO'
};

let regionData = {};
let chaptersByRegion = {};
let selectedRegion = '\uac15\ub0a8';
let zoomLevel = 1;

// Clock
function updateClock(){
  const now = new Date();
  const d = now.toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'});
  const t = now.toLocaleTimeString('en-US',{hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'});
  document.getElementById('clock').textContent = d + ' ' + t;
}
setInterval(updateClock, 1000);
updateClock();

// Canvas map processing
function processMap() {
  const img = document.getElementById('mapImg');
  const canvas = document.getElementById('mapCanvas');
  const mapArea = document.querySelector('.map-area');

  const areaW = mapArea.clientWidth;
  const areaH = mapArea.clientHeight;
  const imgRatio = img.naturalWidth / img.naturalHeight;
  const areaRatio = areaW / areaH;
  let w, h;
  if(areaRatio > imgRatio) { h = Math.floor(areaH * 0.88); w = Math.floor(h * imgRatio); }
  else { w = Math.floor(areaW * 0.88); h = Math.floor(w / imgRatio); }

  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, w, h);

  const imageData = ctx.getImageData(0, 0, w, h);
  const px = imageData.data;
  const len = w * h;

  // Step 1: Classify pixels - map(dark), river(blue), background(light)
  const isMap = new Uint8Array(len);
  const isRiver = new Uint8Array(len);
  for(let i = 0; i < len; i++) {
    const r = px[i*4], g = px[i*4+1], b = px[i*4+2];
    const avg = (r + g + b) / 3;
    // Detect blue river pixels (blue channel dominant)
    if(b > 100 && b > r * 1.5 && b > g * 1.2) {
      isRiver[i] = 1;
    } else if(avg < 100) {
      isMap[i] = 1;
    }
  }

  // Step 2: Remove interior text via flood-fill from edges
  const isExterior = new Uint8Array(len);
  const queue = [];
  for(let x = 0; x < w; x++) {
    if(!isMap[x] && !isRiver[x]) { isExterior[x] = 1; queue.push(x); }
    const b = (h-1)*w+x;
    if(!isMap[b] && !isRiver[b]) { isExterior[b] = 1; queue.push(b); }
  }
  for(let y = 1; y < h-1; y++) {
    const l = y*w;
    if(!isMap[l] && !isRiver[l]) { isExterior[l] = 1; queue.push(l); }
    const r = y*w+w-1;
    if(!isMap[r] && !isRiver[r]) { isExterior[r] = 1; queue.push(r); }
  }
  let qi = 0;
  while(qi < queue.length) {
    const idx = queue[qi++];
    const x = idx % w, y = (idx - x) / w;
    const neighbors = [];
    if(x > 0) neighbors.push(idx-1);
    if(x < w-1) neighbors.push(idx+1);
    if(y > 0) neighbors.push(idx-w);
    if(y < h-1) neighbors.push(idx+w);
    for(const ni of neighbors) {
      if(!isMap[ni] && !isRiver[ni] && !isExterior[ni]) {
        isExterior[ni] = 1;
        queue.push(ni);
      }
    }
  }
  // Interior light pixels (text) -> treat as map
  for(let i = 0; i < len; i++) {
    if(!isMap[i] && !isRiver[i] && !isExterior[i]) isMap[i] = 1;
  }

  // Step 3: Find border pixels
  const isBorder = new Uint8Array(len);
  for(let y = 1; y < h-1; y++) {
    for(let x = 1; x < w-1; x++) {
      const idx = y * w + x;
      if(isMap[idx] || isRiver[idx]) continue;
      if(isMap[idx-1] || isMap[idx+1] || isMap[idx-w] || isMap[idx+w] ||
         isMap[idx-w-1] || isMap[idx-w+1] || isMap[idx+w-1] || isMap[idx+w+1]) {
        isBorder[idx] = 1;
      }
    }
  }

  // Step 4: Dilate borders
  const isBorder2 = new Uint8Array(len);
  for(let y = 1; y < h-1; y++) {
    for(let x = 1; x < w-1; x++) {
      const idx = y * w + x;
      if(isBorder[idx] || isBorder[idx-1] || isBorder[idx+1] || isBorder[idx-w] || isBorder[idx+w]) {
        isBorder2[idx] = 1;
      }
    }
  }

  // Step 5: Render
  const bgColor = 10;
  const fillColor = 34;
  const borderColor = 65;

  for(let i = 0; i < len; i++) {
    const pi = i * 4;
    if(isRiver[i]) {
      // Dark subtle river
      px[pi] = 15; px[pi+1] = 25; px[pi+2] = 50; px[pi+3] = 255;
    } else if(isMap[i]) {
      px[pi] = fillColor; px[pi+1] = fillColor; px[pi+2] = fillColor; px[pi+3] = 255;
    } else if(isBorder2[i]) {
      px[pi] = borderColor; px[pi+1] = borderColor; px[pi+2] = borderColor; px[pi+3] = 255;
    } else {
      px[pi] = bgColor; px[pi+1] = bgColor; px[pi+2] = bgColor; px[pi+3] = 255;
    }
  }

  ctx.putImageData(imageData, 0, 0);
}

// Seoul-only districts from data
const SEOUL_DISTRICTS = ['\uac15\ub0a8','\uc11c\ucd08','\uc131\ub3d9','\ub9c8\ud3ec','\uc1a1\ud30c','\uc911\uad6c','\uc601\ub4f1\ud3ec'];

function generateTestData(){
  const counts = [22,15,14,14,14,5,9];
  const chapters = ['\uc2dc\ub108\uc9c0','\ubbf8\ub77c\ud074','\ubbf8\ub2e4\uc2a4','\ud53c\ub2c9\uc2a4','\ud0c0\uc774\ud0c4','\ub4dc\ub798\uace4','\uc774\uae00','\uc624\uba54\uac00','\uc54c\ud30c','\ube0c\ub808\uc774\ube0c'];
  regionData = {};
  chaptersByRegion = {};
  SEOUL_DISTRICTS.forEach((c,i)=>{
    regionData[c] = counts[i] || Math.floor(Math.random()*10)+3;
    const chs = {};
    const shuffled = [...chapters].sort(()=>Math.random()-0.5).slice(0,5);
    const total = regionData[c];
    let remaining = total;
    shuffled.forEach((ch,j)=>{
      const v = j < shuffled.length-1 ? Math.max(1,Math.floor(remaining/(shuffled.length-j)*(.5+Math.random()))) : remaining;
      chs[ch] = Math.max(1, v);
      remaining -= chs[ch];
      if(remaining < 1) remaining = 1;
    });
    chaptersByRegion[c] = chs;
  });
}

async function loadData(){
  try {
    const res = await fetch(API_URL);
    const data = await res.json();
    const rows = data.data || data;
    if(!rows || !rows.length) throw new Error('No data');
    regionData = {};
    chaptersByRegion = {};
    rows.forEach(r => {
      const region = (r.myRegion || '').trim();
      const chapter = (r.myChapter || '').trim();
      if(!region || !SEOUL_DISTRICTS.includes(region)) return;
      regionData[region] = (regionData[region]||0) + 1;
      if(!chaptersByRegion[region]) chaptersByRegion[region] = {};
      if(chapter) chaptersByRegion[region][chapter] = (chaptersByRegion[region][chapter]||0) + 1;
    });
    if(Object.keys(regionData).length === 0) throw new Error('Empty');
  } catch(e) {
    console.warn('API failed, using test data:', e);
    generateTestData();
  }
  render();
}

function render(){
  renderRegionList();
  renderMarkers();
  renderRightPanel();
  updateTotals();
}

function renderRegionList(){
  const list = document.getElementById('regionList');
  const sorted = Object.entries(regionData).sort((a,b)=>b[1]-a[1]);
  list.innerHTML = sorted.map(([name, count])=>`
    <div class="region-item${name===selectedRegion?' active':''}" onclick="selectRegion('${name}')">
      <div class="region-dot"></div>
      <div class="region-name">${name}</div>
      <div class="region-count">${count}</div>
    </div>
  `).join('');
}

function renderMarkers(){
  const overlay = document.getElementById('markerOverlay');
  overlay.innerHTML = '';
  const canvas = document.getElementById('mapCanvas');
  if(!canvas || !canvas.width) return;
  const mapArea = document.querySelector('.map-area');
  const areaRect = mapArea.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();
  overlay.style.left = (canvasRect.left - areaRect.left) + 'px';
  overlay.style.top = (canvasRect.top - areaRect.top) + 'px';
  overlay.style.width = canvasRect.width + 'px';
  overlay.style.height = canvasRect.height + 'px';

  Object.entries(regionData).forEach(([name, count])=>{
    const pos = DISTRICT_POSITIONS[name];
    if(!pos) return;
    const group = document.createElement('div');
    group.className = 'marker-group' + (name===selectedRegion?' active':'');
    group.style.left = pos.x + '%';
    group.style.top = pos.y + '%';
    group.onclick = () => selectRegion(name);
    group.innerHTML = '<div class="dot"></div><div class="count">' + count + '</div><div class="label">' + name + '</div>';
    overlay.appendChild(group);
  });
}
window.addEventListener('resize', ()=>{ renderMarkers(); });

function renderRightPanel(){
  const en = EN_NAMES[selectedRegion] || selectedRegion;
  const count = regionData[selectedRegion] || 0;
  const total = Object.values(regionData).reduce((a,b)=>a+b,0);
  const pct = total > 0 ? ((count/total)*100).toFixed(1) : 0;
  const quota = 50;
  const fulfillment = Math.round((count/quota)*100);

  document.getElementById('rightRegionName').textContent = en;
  document.getElementById('rightCount').textContent = count;
  document.getElementById('rightBadge').textContent = '+' + pct + '%';
  document.getElementById('quotaBar').style.width = fulfillment + '%';
  document.getElementById('quotaPct').textContent = fulfillment + '%';

  const chapters = chaptersByRegion[selectedRegion] || {};
  const top5 = Object.entries(chapters).sort((a,b)=>b[1]-a[1]).slice(0,5);
  const maxVal = top5.length ? top5[0][1] : 1;
  const chapEl = document.getElementById('chaptersList');
  chapEl.innerHTML = top5.map(([name,cnt])=>`
    <div class="chapter-item">
      <div class="chapter-name">${name}</div>
      <div class="chapter-bar-bg"><div class="chapter-bar-fill" style="width:${(cnt/maxVal)*100}%"></div></div>
      <div class="chapter-count">${cnt}</div>
    </div>
  `).join('');

  const names = ['SEO MIN-JI','KIM JI-YEON','PARK SUNG-HO','LEE HAE-WON','CHOI YUNA'];
  const nameIdx = Math.abs(selectedRegion.charCodeAt(0)) % names.length;
  document.getElementById('spotlightName').textContent = names[nameIdx];
  document.getElementById('spotlightAvatar').textContent = names[nameIdx].charAt(0);
}

function updateTotals(){
  const total = Object.values(regionData).reduce((a,b)=>a+b,0);
  document.getElementById('totalCount').textContent = total;
  const rate = (90 + Math.random()*8).toFixed(1);
  document.getElementById('activeRate').textContent = rate + '%';
}

function selectRegion(name){
  selectedRegion = name;
  render();
}

function zoomIn(){
  zoomLevel = Math.min(zoomLevel * 1.2, 3);
  document.getElementById('mapCanvas').style.transform = 'scale('+zoomLevel+')';
  setTimeout(renderMarkers, 50);
}
function zoomOut(){
  zoomLevel = Math.max(zoomLevel / 1.2, 0.5);
  document.getElementById('mapCanvas').style.transform = 'scale('+zoomLevel+')';
  setTimeout(renderMarkers, 50);
}

// Tab switching
document.getElementById('tabDistrict').onclick = function(){
  this.classList.add('active');
  document.getElementById('tabAll').classList.remove('active');
};
document.getElementById('tabAll').onclick = function(){
  this.classList.add('active');
  document.getElementById('tabDistrict').classList.remove('active');
};

// Init
const mapImg = document.getElementById('mapImg');
function initMap(){
  if(!mapImg.naturalWidth || !mapImg.naturalHeight){
    console.warn('Map image not loaded, retrying...');
    setTimeout(initMap, 200);
    return;
  }
  processMap();
  loadData();
}
mapImg.onerror = function(){ console.error('Map image failed to load'); loadData(); };
if(mapImg.complete && mapImg.naturalWidth > 0){ initMap(); }
else { mapImg.onload = initMap; }

let resizeTimer;
window.addEventListener('resize', ()=>{
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(()=>{
    processMap();
    renderMarkers();
  }, 150);
});
</script>
</body>
</html>'''

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(part1)
    f.write(b64)
    f.write(part2)

print('Written', os.path.getsize(out_path), 'bytes')
