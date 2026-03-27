import re, os

# ── 1. Extract Korea national map SVG ──
with open('korea_map.svg','r',encoding='utf-8') as f:
    korea_svg = f.read()

polylines = re.findall(r'<polyline[^>]*id="([^"]+)"[^>]*points="([^"]+)"[^>]*/?>',korea_svg)
sejong_match = re.search(r'<path[^>]*id="sejong"[^>]*d="([^"]+)"', korea_svg)
sejong_d = sejong_match.group(1) if sejong_match else ''
tx, ty = 106.95522, 19.462687

korea_shapes = []
for pid, pts in polylines:
    nums = re.findall(r'[\-\d\.]+', pts)
    translated = []
    for i in range(0, len(nums)-1, 2):
        x = float(nums[i]) + tx
        y = float(nums[i+1]) + ty
        translated.append(f"{x:.1f},{y:.1f}")
    points_str = " ".join(translated)
    korea_shapes.append(f'<polygon id="{pid}" class="province" points="{points_str}"/>')
if sejong_d:
    korea_shapes.append(f'<g transform="translate({tx},{ty})"><path id="sejong" class="province" d="{sejong_d}"/></g>')
korea_svg_content = "\n".join(korea_shapes)

# ── 2. Extract Seoul districts SVG ──
with open('seoul_districts.svg','r',encoding='utf-8') as f:
    seoul_svg = f.read()

seoul_paths = re.findall(r'<path[^>]*id="([^"]+)"[^>]*d="([^"]+)"[^>]*/>', seoul_svg, re.DOTALL)
if not seoul_paths:
    seoul_paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*id="([^"]+)"[^>]*/>', seoul_svg, re.DOTALL)
    seoul_paths = [(b,a) for a,b in seoul_paths]

seoul_shapes = []
for pid, d in seoul_paths:
    clean_d = ' '.join(d.split())
    seoul_shapes.append(f'<path id="s-{pid}" class="district" d="{clean_d}"/>')
seoul_svg_content = "\n".join(seoul_shapes)

# ── 3. Build HTML ──
html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GUARDIAN - Regional Performance Map</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:"Segoe UI",sans-serif;background:#0a0a0a;color:#fff;overflow:hidden;height:100vh;width:100vw;}}

.topbar{{height:46px;background:#111;border-bottom:1px solid #222;display:flex;align-items:center;justify-content:space-between;padding:0 20px;z-index:100;position:relative;}}
.topbar .brand{{display:flex;align-items:center;gap:10px;}}
.topbar .brand .icon{{width:26px;height:26px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;color:#fff;}}
.topbar .brand span{{font-weight:700;font-size:14px;letter-spacing:4px;color:#c41a2e;}}
.topbar nav{{display:flex;gap:4px;position:absolute;left:50%;transform:translateX(-50%);}}
.topbar nav a{{color:#555;text-decoration:none;font-size:10px;font-weight:600;letter-spacing:1.5px;padding:5px 12px;border-radius:3px;text-transform:uppercase;transition:all .2s;}}
.topbar nav a:hover{{color:#999;}}
.topbar nav a.active{{color:#ccc;background:rgba(255,255,255,0.05);}}
.topbar .clock{{color:#555;font-size:11px;font-weight:500;letter-spacing:0.5px;}}

.main{{display:flex;height:calc(100vh - 46px);}}

/* LEFT SIDEBAR */
.sidebar-left{{width:220px;background:#111;border-right:1px solid #1a1a1a;display:flex;flex-direction:column;overflow:hidden;}}
.profile-card{{padding:14px 16px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;gap:10px;}}
.profile-avatar{{width:32px;height:32px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;}}
.profile-info{{display:flex;flex-direction:column;}}
.profile-name{{font-size:12px;font-weight:700;color:#eee;letter-spacing:0.5px;}}
.profile-sub{{font-size:9px;color:#555;letter-spacing:0.5px;margin-top:1px;}}
.tabs{{display:flex;border-bottom:1px solid #1a1a1a;}}
.tab-btn{{flex:1;padding:9px 0;text-align:center;font-size:9px;font-weight:700;letter-spacing:1.5px;color:#555;background:transparent;border:none;cursor:pointer;text-transform:uppercase;transition:all .2s;border-bottom:2px solid transparent;}}
.tab-btn.active{{color:#ccc;border-bottom-color:#c41a2e;background:rgba(196,26,46,0.05);}}
.tab-btn:hover{{color:#888;}}
.section-header{{padding:12px 16px 8px;font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;}}
.region-list{{flex:1;overflow-y:auto;padding:0 8px 8px;}}
.region-list::-webkit-scrollbar{{width:3px;}}
.region-list::-webkit-scrollbar-track{{background:transparent;}}
.region-list::-webkit-scrollbar-thumb{{background:#333;border-radius:2px;}}
.region-item{{display:flex;align-items:center;padding:7px 10px;margin-bottom:1px;border-radius:4px;cursor:pointer;transition:all .15s;border-left:2px solid transparent;gap:8px;}}
.region-item:hover{{background:rgba(255,255,255,0.03);}}
.region-item.active{{background:rgba(196,26,46,0.08);border-left-color:#c41a2e;}}
.region-dot{{width:6px;height:6px;background:#c41a2e;border-radius:50%;flex-shrink:0;}}
.region-name{{flex:1;font-size:12px;color:#bbb;font-weight:500;}}
.region-item.active .region-name{{color:#fff;}}
.region-count{{font-size:10px;color:#666;font-weight:600;background:#1a1a1a;padding:1px 7px;border-radius:8px;min-width:24px;text-align:center;}}
.region-item.active .region-count{{background:rgba(196,26,46,0.2);color:#e88;}}
.deploy-btn{{margin:10px 12px;padding:10px;background:#c41a2e;color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:2px;cursor:pointer;text-transform:uppercase;transition:all .2s;}}
.deploy-btn:hover{{background:#d42a3e;}}

/* CENTER MAP */
.map-center{{flex:1;display:flex;flex-direction:column;position:relative;background:#0a0a0a;}}
.map-area{{flex:1;position:relative;overflow:hidden;}}
.dot-grid{{position:absolute;inset:0;background-image:radial-gradient(circle,#1a1a1a 1px,transparent 1px);background-size:24px 24px;opacity:0.5;}}
.scan-line{{position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(196,26,46,0.15),transparent);animation:scanMove 6s linear infinite;z-index:5;pointer-events:none;}}
@keyframes scanMove{{0%{{top:0;}}100%{{top:100%;}}}}
.map-svg-wrap{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;}}
.map-svg-wrap svg{{height:88%;width:auto;transition:transform .2s;}}
.province{{fill:#1e1e1e;stroke:#333;stroke-width:1.5;transition:fill .2s, stroke .2s;cursor:pointer;}}
.province:hover{{fill:#2a2a2a;}}
.province.highlight{{fill:#2a1015;stroke:#c41a2e;stroke-width:2;}}
.province.has-detail{{cursor:pointer;}}
.province.has-detail:hover{{fill:#1a2a1a;stroke:#4a4;}}

.marker-overlay{{position:absolute;inset:0;pointer-events:none;}}
.marker-group{{position:absolute;transform:translate(-50%,-50%);cursor:pointer;z-index:10;pointer-events:auto;display:flex;flex-direction:column;align-items:center;}}
.marker-group .dot{{width:8px;height:8px;background:#c41a2e;border-radius:50%;box-shadow:0 0 6px rgba(196,26,46,0.5);transition:all .2s;}}
.marker-group:hover .dot{{transform:scale(1.4);box-shadow:0 0 12px rgba(196,26,46,0.8);}}
.marker-group.active .dot{{animation:pulse 1.5s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 6px rgba(196,26,46,0.5);}}50%{{box-shadow:0 0 16px rgba(196,26,46,0.9);}}}}
.marker-group .label{{margin-top:3px;font-size:9px;font-weight:700;color:#999;letter-spacing:0.5px;white-space:nowrap;text-shadow:0 1px 3px rgba(0,0,0,0.8);}}
.marker-group.active .label{{color:#fff;}}
.marker-group .count{{font-size:10px;font-weight:800;color:#c41a2e;text-shadow:0 1px 3px rgba(0,0,0,0.8);}}
/* Province label (for clickable provinces like Seoul) */
.province-label{{position:absolute;transform:translate(-50%,-50%);pointer-events:auto;cursor:pointer;z-index:10;display:flex;flex-direction:column;align-items:center;}}
.province-label .name{{font-size:10px;font-weight:800;color:#6c6;letter-spacing:1px;text-shadow:0 1px 3px rgba(0,0,0,0.8);}}
.province-label .sub{{font-size:8px;color:#585;letter-spacing:0.5px;margin-top:1px;}}

.zoom-controls{{position:absolute;left:14px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:2px;z-index:20;}}
.zoom-btn{{width:28px;height:28px;background:#1a1a1a;border:1px solid #333;color:#888;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;transition:all .2s;}}
.zoom-btn:first-child{{border-radius:4px 4px 0 0;}}
.zoom-btn:last-child{{border-radius:0 0 4px 4px;}}
.zoom-btn:hover{{background:#252525;color:#ccc;}}

.bottom-stats{{height:60px;display:flex;align-items:center;justify-content:center;gap:60px;border-top:1px solid #1a1a1a;background:#0d0d0d;}}
.stat-big{{display:flex;flex-direction:column;align-items:center;}}
.stat-big .val{{font-size:28px;font-weight:800;color:#fff;letter-spacing:1px;}}
.stat-big .label{{font-size:8px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;}}

/* RIGHT PANEL */
.sidebar-right{{width:300px;background:#111;border-left:1px solid #1a1a1a;display:flex;flex-direction:column;overflow-y:auto;}}
.sidebar-right::-webkit-scrollbar{{width:3px;}}
.sidebar-right::-webkit-scrollbar-track{{background:transparent;}}
.sidebar-right::-webkit-scrollbar-thumb{{background:#333;border-radius:2px;}}
.right-header{{padding:16px 20px 6px;font-size:9px;font-weight:600;letter-spacing:2px;color:#444;text-transform:uppercase;}}
.right-region-name{{padding:0 20px;font-size:26px;font-weight:800;color:#fff;letter-spacing:1px;}}
.right-big-number{{padding:12px 20px 0;display:flex;align-items:baseline;gap:10px;}}
.right-big-number .num{{font-size:42px;font-weight:800;color:#c41a2e;}}
.right-big-number .badge{{font-size:11px;font-weight:700;color:#4caf50;background:rgba(76,175,80,0.1);padding:3px 8px;border-radius:10px;}}
.right-label{{padding:2px 20px 0;font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;}}
.quota-section{{padding:16px 20px 0;}}
.quota-title{{font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;margin-bottom:8px;}}
.quota-bar-bg{{height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden;}}
.quota-bar-fill{{height:100%;background:#c41a2e;border-radius:3px;transition:width .5s;}}
.quota-pct{{font-size:11px;color:#888;margin-top:4px;text-align:right;font-weight:600;}}
.chapters-section{{padding:16px 20px 0;}}
.chapters-title{{font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;margin-bottom:10px;}}
.chapter-item{{display:flex;align-items:center;margin-bottom:8px;gap:8px;}}
.chapter-name{{width:50px;font-size:11px;color:#999;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.chapter-bar-bg{{flex:1;height:8px;background:#1a1a1a;border-radius:2px;overflow:hidden;}}
.chapter-bar-fill{{height:100%;background:#c41a2e;border-radius:2px;transition:width .5s;}}
.chapter-count{{font-size:10px;color:#666;font-weight:600;width:24px;text-align:right;flex-shrink:0;}}
.spotlight-section{{margin-top:auto;padding:14px 20px;border-top:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between;}}
.spotlight-label{{font-size:8px;color:#444;letter-spacing:1.5px;text-transform:uppercase;}}
.spotlight-name{{font-size:12px;color:#ccc;font-weight:600;margin-top:2px;}}
.spotlight-avatar{{width:32px;height:32px;background:#c41a2e;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;}}

/* ── DETAIL MODAL ── */
.detail-modal{{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,0.85);align-items:center;justify-content:center;}}
.detail-modal.open{{display:flex;}}
.detail-content{{background:#111;border:1px solid #333;border-radius:8px;width:70vw;height:80vh;max-width:900px;display:flex;flex-direction:column;position:relative;}}
.detail-header{{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid #222;}}
.detail-title{{font-size:18px;font-weight:800;letter-spacing:2px;color:#fff;}}
.detail-close{{width:32px;height:32px;background:#222;border:1px solid #444;border-radius:4px;color:#999;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;}}
.detail-close:hover{{background:#333;color:#fff;}}
.detail-body{{flex:1;display:flex;position:relative;overflow:hidden;}}
.detail-map{{flex:1;position:relative;display:flex;align-items:center;justify-content:center;}}
.detail-map svg{{height:85%;width:auto;}}
.district{{fill:#1e1e1e;stroke:#333;stroke-width:1.5;transition:fill .2s, stroke .2s;cursor:pointer;}}
.district:hover{{fill:#2a2a2a;}}
.district.highlight{{fill:#2a1015;stroke:#c41a2e;stroke-width:2;}}
.detail-marker-overlay{{position:absolute;inset:0;pointer-events:none;}}
.detail-info{{width:240px;padding:20px;border-left:1px solid #222;overflow-y:auto;}}
.detail-info .di-region{{font-size:20px;font-weight:800;color:#fff;margin-bottom:4px;}}
.detail-info .di-count{{font-size:36px;font-weight:800;color:#c41a2e;}}
.detail-info .di-label{{font-size:8px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;}}
.detail-info .di-section{{margin-top:16px;}}
.detail-info .di-section-title{{font-size:9px;font-weight:700;letter-spacing:2px;color:#444;text-transform:uppercase;margin-bottom:8px;}}
.di-list-item{{display:flex;align-items:center;padding:5px 0;gap:6px;cursor:pointer;transition:background .15s;border-radius:3px;}}
.di-list-item:hover{{background:rgba(255,255,255,0.03);}}
.di-list-item.active{{color:#fff;}}
.di-list-item .di-dot{{width:5px;height:5px;background:#c41a2e;border-radius:50%;}}
.di-list-item .di-name{{flex:1;font-size:11px;color:#bbb;}}
.di-list-item.active .di-name{{color:#fff;}}
.di-list-item .di-cnt{{font-size:10px;color:#666;font-weight:600;}}
</style>
</head>
<body>

<div class="topbar">
  <div class="brand"><div class="icon">G</div><span>GUARDIAN</span></div>
  <nav>
    <a href="#">REGIONAL</a>
    <a href="#">DIAGNOSTICS</a>
    <a href="#" class="active">MAP</a>
    <a href="#">SETTINGS</a>
  </nav>
  <div class="clock" id="clock"></div>
</div>

<div class="main">
  <div class="sidebar-left">
    <div class="profile-card">
      <div class="profile-avatar">P</div>
      <div class="profile-info">
        <div class="profile-name">Protocol Alpha</div>
        <div class="profile-sub">Command Center v2.0</div>
      </div>
    </div>
    <div class="tabs">
      <button class="tab-btn" id="tabNational">NATIONAL</button>
      <button class="tab-btn active" id="tabRegional">REGIONAL</button>
    </div>
    <div class="section-header">REGIONAL ASSETS</div>
    <div class="region-list" id="regionList"></div>
    <button class="deploy-btn">DEPLOY MONITOR</button>
  </div>

  <div class="map-center">
    <div class="map-area">
      <div class="dot-grid"></div>
      <div class="scan-line"></div>
      <div class="map-svg-wrap">
        <svg id="mapSvg" viewBox="0 0 800 1200" xmlns="http://www.w3.org/2000/svg">
{korea_svg_content}
        </svg>
      </div>
      <div class="marker-overlay" id="markerOverlay"></div>
      <div class="zoom-controls">
        <div class="zoom-btn" onclick="zoomIn()">+</div>
        <div class="zoom-btn" onclick="zoomOut()">&minus;</div>
      </div>
    </div>
    <div class="bottom-stats">
      <div class="stat-big"><div class="val" id="totalCount">0</div><div class="label">TOTAL GUARDIANS</div></div>
      <div class="stat-big"><div class="val" id="activeRate">0%</div><div class="label">ACTIVE RATE</div></div>
    </div>
  </div>

  <div class="sidebar-right">
    <div class="right-header">SELECTED REGION</div>
    <div class="right-region-name" id="rightRegionName">-</div>
    <div class="right-big-number"><div class="num" id="rightCount">0</div><div class="badge" id="rightBadge">+0%</div></div>
    <div class="right-label">GUARDIANS IN REGION</div>
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
      <div><div class="spotlight-label">SECTOR MVP SPOTLIGHT</div><div class="spotlight-name" id="spotlightName">-</div></div>
      <div class="spotlight-avatar" id="spotlightAvatar">-</div>
    </div>
  </div>
</div>

<!-- ── DETAIL MAP MODAL ── -->
<div class="detail-modal" id="detailModal">
  <div class="detail-content">
    <div class="detail-header">
      <div class="detail-title" id="detailTitle">SEOUL</div>
      <div class="detail-close" id="detailClose">&times;</div>
    </div>
    <div class="detail-body">
      <div class="detail-map">
        <svg id="detailSvg" viewBox="0 0 1400 1400" xmlns="http://www.w3.org/2000/svg" style="display:none;">
{seoul_svg_content}
        </svg>
        <div class="detail-marker-overlay" id="detailMarkerOverlay"></div>
      </div>
      <div class="detail-info">
        <div class="di-region" id="diRegion">SEOUL</div>
        <div class="di-count" id="diCount">0</div>
        <div class="di-label">TOTAL IN REGION</div>
        <div class="di-section">
          <div class="di-section-title">DISTRICTS</div>
          <div id="diList"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const API_URL = "https://script.google.com/macros/s/AKfycbyXXPPtJ-5T98hc63xxfLXtKqfvTK3YaUkxTyNjEbNofiWyAGf7N2GT6i4k1X2xDKUXEw/exec?action=getData";

// ── National map: city positions (SVG coords 800x1200) ──
// Non-Seoul cities shown directly on national map
const NATIONAL_MARKERS = {{
  "\uc778\ucc9c": {{x:205,y:257}},
  "\uace0\uc591": {{x:245,y:195}},
  "\uc131\ub0a8": {{x:290,y:295}},
  "\uc218\uc6d0": {{x:255,y:340}},
  "\uc6a9\uc778": {{x:310,y:335}},
  "\ud654\uc131": {{x:220,y:338}},
  "\ucc9c\uc548": {{x:275,y:395}},
  "\ub300\uc804": {{x:332,y:503}},
  "\ub300\uad6c": {{x:520,y:624}},
  "\ubd80\uc0b0": {{x:618,y:750}}
}};

// Seoul province label position on national map
const SEOUL_LABEL_POS = {{x:256,y:249}};

// ── Detail map configs ──
// Each province that has a detail popup
const DETAIL_MAPS = {{
  "seoul": {{
    title: "SEOUL",
    svgId: "detailSvg",
    viewBox: "0 0 1400 1400",
    // Korean city name -> SVG district id (s-prefix)
    districtMap: {{
      "\uac15\ub0a8": "s-Gangnam-gu",
      "\uc11c\ucd08": "s-Seocho-gu",
      "\uc131\ub3d9": "s-Seongdong-gu",
      "\ub9c8\ud3ec": "s-Mapo-gu",
      "\uc1a1\ud30c": "s-Songpa-gu",
      "\uc911\uad6c": "s-Jung-gu",
      "\uc601\ub4f1\ud3ec": "s-Yeongdeungpo-gu_1_"
    }},
    // Cities that belong to this detail map (removed from national)
    cities: ["\uac15\ub0a8","\uc11c\ucd08","\uc131\ub3d9","\ub9c8\ud3ec","\uc1a1\ud30c","\uc911\uad6c","\uc601\ub4f1\ud3ec"]
  }}
}};

// Province SVG id -> detail map key
const PROVINCE_DETAIL = {{
  "seoul": "seoul"
}};

// Province SVG id -> cities (for provinces without detail maps)
const PROVINCE_CITY_MAP = {{
  "incheon": ["\uc778\ucc9c"],
  "gyeonggi": ["\uace0\uc591","\uc131\ub0a8","\uc218\uc6d0","\uc6a9\uc778","\ud654\uc131"],
  "chungnam": ["\ucc9c\uc548"],
  "daejeon": ["\ub300\uc804"],
  "daegu": ["\ub300\uad6c"],
  "busan": ["\ubd80\uc0b0"]
}};

const EN_NAMES = {{
  "\uac15\ub0a8":"GANGNAM","\ub300\uad6c":"DAEGU","\ub300\uc804":"DAEJEON","\uc11c\ucd08":"SEOCHO","\uc131\ub3d9":"SEONGDONG",
  "\ub9c8\ud3ec":"MAPO","\ubd80\uc0b0":"BUSAN","\uc1a1\ud30c":"SONGPA","\uc218\uc6d0":"SUWON","\uc6a9\uc778":"YONGIN",
  "\uc601\ub4f1\ud3ec":"YEONGDEUNGPO","\uc778\ucc9c":"INCHEON","\uace0\uc591":"GOYANG","\ud654\uc131":"HWASEONG",
  "\uc911\uad6c":"JUNGGU","\ucc9c\uc548":"CHEONAN","\uc131\ub0a8":"SEONGNAM"
}};

let regionData = {{}};
let chaptersByRegion = {{}};
let selectedRegion = "\uc1a1\ud30c";
let zoomLevel = 1;
let detailSelectedCity = null;

// ── Clock ──
function updateClock(){{
  const now = new Date();
  const d = now.toLocaleDateString("en-US",{{year:"numeric",month:"short",day:"numeric"}});
  const t = now.toLocaleTimeString("en-US",{{hour12:false,hour:"2-digit",minute:"2-digit",second:"2-digit"}});
  document.getElementById("clock").textContent = d + " " + t;
}}
setInterval(updateClock, 1000);
updateClock();

// ── Province click → open detail or select region ──
document.querySelectorAll(".province").forEach(el => {{
  el.addEventListener("click", () => {{
    const provId = el.id;
    if(PROVINCE_DETAIL[provId]) {{
      openDetailMap(PROVINCE_DETAIL[provId]);
    }} else {{
      const cities = PROVINCE_CITY_MAP[provId];
      if(cities && cities.length > 0) selectRegion(cities[0]);
    }}
  }});
}});

// Mark provinces that have detail maps
Object.keys(PROVINCE_DETAIL).forEach(provId => {{
  const el = document.getElementById(provId);
  if(el) el.classList.add("has-detail");
}});

// ── Data ──
function generateTestData(){{
  const cities = ["\uac15\ub0a8","\ub300\uad6c","\ub300\uc804","\uc11c\ucd08","\uc131\ub3d9","\ub9c8\ud3ec","\ubd80\uc0b0","\uc1a1\ud30c","\uc218\uc6d0","\uc6a9\uc778","\uc601\ub4f1\ud3ec","\uc778\ucc9c","\uace0\uc591","\ud654\uc131","\uc911\uad6c","\ucc9c\uc548"];
  const chapters = ["\uc2dc\ub108\uc9c0","\ubbf8\ub77c\ud074","\ubbf8\ub2e4\uc2a4","\ud53c\ub2c9\uc2a4","\ud0c0\uc774\ud0c4","\ub4dc\ub798\uace4","\uc774\uae00","\uc624\uba54\uac00","\uc54c\ud30c","\ube0c\ub808\uc774\ube0c"];
  const counts = [22,18,16,15,14,14,12,14,11,10,9,8,7,6,5,4];
  regionData = {{}};
  chaptersByRegion = {{}};
  cities.forEach((c,i)=>{{
    regionData[c] = counts[i] || Math.floor(Math.random()*10)+3;
    const chs = {{}};
    const shuffled = [...chapters].sort(()=>Math.random()-0.5).slice(0,5);
    const total = regionData[c];
    let remaining = total;
    shuffled.forEach((ch,j)=>{{
      const v = j < shuffled.length-1 ? Math.max(1,Math.floor(remaining/(shuffled.length-j)*(.5+Math.random()))) : remaining;
      chs[ch] = Math.max(1, v);
      remaining -= chs[ch];
      if(remaining < 1) remaining = 1;
    }});
    chaptersByRegion[c] = chs;
  }});
}}

async function loadData(){{
  try {{
    const res = await fetch(API_URL);
    const data = await res.json();
    const rows = data.data || data;
    if(!rows || !rows.length) throw new Error("No data");
    regionData = {{}};
    chaptersByRegion = {{}};
    rows.forEach(r => {{
      const region = (r.myRegion || "").trim();
      const chapter = (r.myChapter || "").trim();
      if(!region) return;
      regionData[region] = (regionData[region]||0) + 1;
      if(!chaptersByRegion[region]) chaptersByRegion[region] = {{}};
      if(chapter) chaptersByRegion[region][chapter] = (chaptersByRegion[region][chapter]||0) + 1;
    }});
    if(Object.keys(regionData).length === 0) throw new Error("Empty");
  }} catch(e) {{
    console.warn("API failed, using test data:", e);
    generateTestData();
  }}
  render();
}}

// ── Render national map ──
function render(){{
  renderRegionList();
  renderMarkers();
  highlightProvince();
  renderRightPanel();
  updateTotals();
}}

function highlightProvince(){{
  document.querySelectorAll(".province").forEach(el=>el.classList.remove("highlight"));
  // Find which province the selected region belongs to
  for(const [provId, cities] of Object.entries(PROVINCE_CITY_MAP)){{
    if(cities.includes(selectedRegion)){{
      const el = document.getElementById(provId);
      if(el) el.classList.add("highlight");
      return;
    }}
  }}
  // Check detail maps
  for(const [key, cfg] of Object.entries(DETAIL_MAPS)){{
    if(cfg.cities.includes(selectedRegion)){{
      // Highlight the province that owns this detail
      for(const [provId, detailKey] of Object.entries(PROVINCE_DETAIL)){{
        if(detailKey === key){{
          const el = document.getElementById(provId);
          if(el) el.classList.add("highlight");
        }}
      }}
      return;
    }}
  }}
}}

function renderRegionList(){{
  const list = document.getElementById("regionList");
  const sorted = Object.entries(regionData).sort((a,b)=>b[1]-a[1]);
  list.innerHTML = sorted.map(([name, count])=>{{
    const ac = name===selectedRegion?" active":"";
    return '<div class="region-item'+ac+'" data-rg="'+name+'"><div class="region-dot"></div><div class="region-name">'+name+'</div><div class="region-count">'+count+'</div></div>';
  }}).join("");
  list.querySelectorAll(".region-item").forEach(el=>{{
    el.onclick = ()=> selectRegion(el.dataset.rg);
  }});
}}

function renderMarkers(){{
  const overlay = document.getElementById("markerOverlay");
  overlay.innerHTML = "";
  const svg = document.getElementById("mapSvg");
  if(!svg) return;
  const svgRect = svg.getBoundingClientRect();
  const mapArea = document.querySelector(".map-area");
  const areaRect = mapArea.getBoundingClientRect();
  const scaleX = svgRect.width / 800;
  const scaleY = svgRect.height / 1200;

  // Non-Seoul markers
  Object.entries(regionData).forEach(([name, count])=>{{
    const pos = NATIONAL_MARKERS[name];
    if(!pos) return;
    const screenX = svgRect.left - areaRect.left + pos.x * scaleX;
    const screenY = svgRect.top - areaRect.top + pos.y * scaleY;
    const group = document.createElement("div");
    group.className = "marker-group" + (name===selectedRegion?" active":"");
    group.style.left = screenX + "px";
    group.style.top = screenY + "px";
    group.onclick = () => selectRegion(name);
    group.innerHTML = '<div class="dot"></div><div class="count">' + count + '</div><div class="label">' + name + '</div>';
    overlay.appendChild(group);
  }});

  // Seoul aggregate label (clickable)
  const seoulCfg = DETAIL_MAPS["seoul"];
  if(seoulCfg){{
    const seoulTotal = seoulCfg.cities.reduce((sum,c)=>(sum + (regionData[c]||0)), 0);
    const sx = svgRect.left - areaRect.left + SEOUL_LABEL_POS.x * scaleX;
    const sy = svgRect.top - areaRect.top + SEOUL_LABEL_POS.y * scaleY;
    const lbl = document.createElement("div");
    lbl.className = "province-label";
    lbl.style.left = sx + "px";
    lbl.style.top = sy + "px";
    lbl.onclick = () => openDetailMap("seoul");
    lbl.innerHTML = '<div class="name">\uc11c\uc6b8 ' + seoulTotal + '</div><div class="sub">CLICK TO EXPAND</div>';
    overlay.appendChild(lbl);
  }}
}}
window.addEventListener("resize", ()=>{{ renderMarkers(); }});

function renderRightPanel(){{
  const en = EN_NAMES[selectedRegion] || selectedRegion;
  const count = regionData[selectedRegion] || 0;
  const total = Object.values(regionData).reduce((a,b)=>a+b,0);
  const pct = total > 0 ? ((count/total)*100).toFixed(1) : 0;
  const quota = 100;
  const fulfillment = Math.round((count/quota)*100);
  document.getElementById("rightRegionName").textContent = en;
  document.getElementById("rightCount").textContent = count;
  document.getElementById("rightBadge").textContent = "+" + pct + "%";
  document.getElementById("quotaBar").style.width = fulfillment + "%";
  document.getElementById("quotaPct").textContent = fulfillment + "%";
  const chapters = chaptersByRegion[selectedRegion] || {{}};
  const top5 = Object.entries(chapters).sort((a,b)=>b[1]-a[1]).slice(0,5);
  const maxVal = top5.length ? top5[0][1] : 1;
  document.getElementById("chaptersList").innerHTML = top5.map(([name,cnt])=>
    '<div class="chapter-item"><div class="chapter-name">'+name+'</div><div class="chapter-bar-bg"><div class="chapter-bar-fill" style="width:'+(cnt/maxVal)*100+'%"></div></div><div class="chapter-count">'+cnt+'</div></div>'
  ).join("");
  const names = ["SEO MIN-JI","KIM JI-YEON","PARK SUNG-HO","LEE HAE-WON","CHOI YUNA"];
  const nameIdx = Math.abs(selectedRegion.charCodeAt(0)) % names.length;
  document.getElementById("spotlightName").textContent = names[nameIdx];
  document.getElementById("spotlightAvatar").textContent = names[nameIdx].charAt(0);
}}

function updateTotals(){{
  const total = Object.values(regionData).reduce((a,b)=>a+b,0);
  document.getElementById("totalCount").textContent = total;
  const rate = (90 + Math.random()*8).toFixed(1);
  document.getElementById("activeRate").textContent = rate + "%";
}}

function selectRegion(name){{
  selectedRegion = name;
  render();
}}

function zoomIn(){{
  zoomLevel = Math.min(zoomLevel * 1.2, 3);
  document.querySelector(".map-svg-wrap svg").style.transform = "scale("+zoomLevel+")";
  setTimeout(renderMarkers, 50);
}}
function zoomOut(){{
  zoomLevel = Math.max(zoomLevel / 1.2, 0.5);
  document.querySelector(".map-svg-wrap svg").style.transform = "scale("+zoomLevel+")";
  setTimeout(renderMarkers, 50);
}}

document.getElementById("tabNational").onclick = function(){{
  this.classList.add("active");
  document.getElementById("tabRegional").classList.remove("active");
}};
document.getElementById("tabRegional").onclick = function(){{
  this.classList.add("active");
  document.getElementById("tabNational").classList.remove("active");
}};

// ── DETAIL MAP MODAL ──
function openDetailMap(key){{
  const cfg = DETAIL_MAPS[key];
  if(!cfg) return;
  const modal = document.getElementById("detailModal");
  const svg = document.getElementById(cfg.svgId);
  document.getElementById("detailTitle").textContent = cfg.title;

  // Show the correct SVG
  document.querySelectorAll(".detail-map svg").forEach(s=>s.style.display="none");
  svg.style.display = "";

  // Set first city as selected
  detailSelectedCity = cfg.cities[0];

  modal.classList.add("open");
  // Wait for layout then render detail markers
  requestAnimationFrame(()=>{{
    renderDetailMap(key);
  }});
}}

function closeDetailMap(){{
  document.getElementById("detailModal").classList.remove("open");
}}
document.getElementById("detailClose").onclick = closeDetailMap;
document.getElementById("detailModal").onclick = function(e){{
  if(e.target === this) closeDetailMap();
}};

function renderDetailMap(key){{
  const cfg = DETAIL_MAPS[key];
  if(!cfg) return;

  // Highlight selected district
  document.querySelectorAll(".district").forEach(el=>el.classList.remove("highlight"));
  if(detailSelectedCity && cfg.districtMap[detailSelectedCity]){{
    const el = document.getElementById(cfg.districtMap[detailSelectedCity]);
    if(el) el.classList.add("highlight");
  }}

  // District click handlers
  Object.entries(cfg.districtMap).forEach(([city, svgId])=>{{
    const el = document.getElementById(svgId);
    if(el){{
      el.onclick = ()=>{{
        detailSelectedCity = city;
        selectedRegion = city;
        renderDetailMap(key);
        render();
      }};
    }}
  }});

  // Render markers using getBBox
  const overlay = document.getElementById("detailMarkerOverlay");
  overlay.innerHTML = "";
  const svg = document.getElementById(cfg.svgId);
  const svgRect = svg.getBoundingClientRect();
  const mapDiv = svg.closest(".detail-map");
  const mapRect = mapDiv.getBoundingClientRect();
  // SVG viewBox
  const vb = svg.viewBox.baseVal;

  cfg.cities.forEach(city=>{{
    const svgElId = cfg.districtMap[city];
    if(!svgElId) return;
    const el = document.getElementById(svgElId);
    if(!el) return;
    const bbox = el.getBBox();
    // Center of district in SVG coords
    const cx = bbox.x + bbox.width/2;
    const cy = bbox.y + bbox.height/2;
    // Convert to screen coords
    const scaleX = svgRect.width / vb.width;
    const scaleY = svgRect.height / vb.height;
    const screenX = svgRect.left - mapRect.left + cx * scaleX;
    const screenY = svgRect.top - mapRect.top + cy * scaleY;
    const count = regionData[city] || 0;

    const group = document.createElement("div");
    group.className = "marker-group" + (city===detailSelectedCity?" active":"");
    group.style.left = screenX + "px";
    group.style.top = screenY + "px";
    group.style.pointerEvents = "auto";
    group.onclick = ()=>{{
      detailSelectedCity = city;
      selectedRegion = city;
      renderDetailMap(key);
      render();
    }};
    group.innerHTML = '<div class="dot"></div><div class="count">' + count + '</div><div class="label">' + city + '</div>';
    overlay.appendChild(group);
  }});

  // Render detail info panel
  const totalInRegion = cfg.cities.reduce((s,c)=>s+(regionData[c]||0),0);
  document.getElementById("diRegion").textContent = cfg.title;
  document.getElementById("diCount").textContent = totalInRegion;
  const diList = document.getElementById("diList");
  const sorted = cfg.cities.map(c=>[c, regionData[c]||0]).sort((a,b)=>b[1]-a[1]);
  diList.innerHTML = sorted.map(([c,cnt])=>{{
    const ac = c===detailSelectedCity?" active":"";
    return '<div class="di-list-item'+ac+'" data-city="'+c+'"><div class="di-dot"></div><div class="di-name">'+c+'</div><div class="di-cnt">'+cnt+'</div></div>';
  }}).join("");
  diList.querySelectorAll(".di-list-item").forEach(el=>{{
    el.onclick = ()=> detailSelectCity(el.dataset.city);
  }});
}}

function detailSelectCity(city){{
  detailSelectedCity = city;
  selectedRegion = city;
  // Find which detail map is open
  for(const [key,cfg] of Object.entries(DETAIL_MAPS)){{
    if(cfg.cities.includes(city)){{
      renderDetailMap(key);
      break;
    }}
  }}
  render();
}}

// Escape key closes modal
document.addEventListener("keydown", (e)=>{{
  if(e.key === "Escape") closeDetailMap();
}});

// ── Init ──
loadData();
</script>
</body>
</html>'''

with open('map-preview-svg.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Written {os.path.getsize("map-preview-svg.html")} bytes')
