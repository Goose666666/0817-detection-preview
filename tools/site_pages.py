# -*- coding: utf-8 -*-
u"""预览站的两个页面模板。图片和框分开存，框按比例定位在图片上。"""

INDEX = u"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;padding:28px 34px 60px;background:#1b1d21;color:#e8e8e8;
     font:15px/1.7 "Microsoft YaHei",sans-serif}
h1{font-size:24px;margin:0 0 6px}
h2{font-size:18px;margin:34px 0 12px;font-weight:600}
a{color:#7ab8ff;text-decoration:none}
a:hover{text-decoration:underline}
table{border-collapse:collapse;margin:0}
th,td{padding:7px 16px;text-align:left;border-bottom:1px solid #2e3238;white-space:nowrap}
th{color:#9aa3ad;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.wrap{max-width:1100px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{background:#24272c;border-radius:8px;padding:14px 16px}
.card a{font-size:17px}
.card .m{color:#9aa3ad;font-size:14px;margin-top:4px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:8px;
    vertical-align:-1px}
.top{color:#9aa3ad}
</style></head><body><div class="wrap">
<h1>__TITLE__</h1>
<p class="top">__SUB__</p>

<h2>按序列查看</h2>
<div class="cards">__CARDS__</div>

<h2>类别</h2>
<table><tr><th>号</th><th>编号</th><th>名称</th><th class="n">图片</th><th class="n">实例</th></tr>
__CLSROWS__</table>

<h2>文件夹</h2>
<table><tr><th>文件夹</th><th>内容</th><th class="n">图片</th><th class="n">框</th></tr>
__FOLDROWS__</table>
</div></body></html>
"""

VIEW = u"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 "Microsoft YaHei",sans-serif;background:#1b1d21;color:#e8e8e8;
     display:flex;height:100vh;overflow:hidden}
#left{flex:1;display:flex;flex-direction:column;min-width:0}
#bar{padding:10px 14px;background:#24272c;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
#bar a.home{color:#7ab8ff;text-decoration:none}
select,button{font:15px "Microsoft YaHei",sans-serif;padding:7px 16px;border:0;border-radius:5px;
              background:#3a3f47;color:#e8e8e8;cursor:pointer}
button:hover,select:hover{background:#4a5058}
button.on{background:#3d5a80}
#pos{font-variant-numeric:tabular-nums;min-width:84px;text-align:center}
#stage{flex:1;overflow:auto;display:flex;align-items:center;justify-content:center;background:#101215}
#wrap{position:relative;line-height:0}
#im{display:block;width:100%;height:100%}
.bx{position:absolute;border:2px solid;pointer-events:none}
.lb{position:absolute;top:-20px;left:-2px;font-size:12px;line-height:16px;padding:1px 5px;
    border-radius:3px;white-space:nowrap;color:#111}
#right{width:250px;background:#24272c;overflow:auto;padding:12px 10px;flex:none}
.cls{display:flex;align-items:center;gap:9px;padding:6px 8px;border-radius:4px;cursor:pointer}
.cls:hover{background:#31353c}
.cls.off{opacity:.35}
.sw{width:15px;height:15px;border-radius:3px;flex:none}
.ct{margin-left:auto;font-variant-numeric:tabular-nums;color:#9aa3ad}
#films{height:92px;background:#24272c;display:flex;gap:5px;overflow-x:auto;padding:7px;flex:none}
#films img{height:100%;border:3px solid transparent;cursor:pointer;border-radius:3px}
#films img.on{border-color:#4da3ff}
</style></head><body>
<div id="left">
  <div id="bar">
    <a class="home" href="index.html">全部序列</a>
    <select id="gsel"></select>
    <button onclick="go(-1)">上一张</button>
    <button onclick="go(1)">下一张</button>
    <span id="pos"></span>
    <button id="tb" class="on" onclick="toggleBox()">框</button>
    <button id="tl" class="on" onclick="toggleLab()">名称</button>
  </div>
  <div id="stage"><div id="wrap"><img id="im" alt=""><div id="ov"></div></div></div>
  <div id="films"></div>
</div>
<div id="right"><div id="legend"></div></div>
<script>
const CLS = __CLS__, COLORS = __COLORS__, GROUPS = __GROUPS__;
let D = null, i = 0, showBox = true, showLab = true, hidden = new Set();

function qs(k){ return new URLSearchParams(location.search).get(k); }
function gid(){ return qs('g') || GROUPS[0][0]; }

const sel = document.getElementById('gsel');
GROUPS.forEach(function(g){
  const o = document.createElement('option');
  o.value = g[0]; o.textContent = g[1] + '  ' + g[2] + ' 张';
  sel.appendChild(o);
});
sel.value = gid();
sel.onchange = function(){ location.search = '?g=' + sel.value; };

fetch('data/' + gid() + '.json').then(function(r){ return r.json(); }).then(function(d){
  D = d;
  document.title = d.group + ' 标注预览';
  films();
  show(0);
});

function films(){
  const box = document.getElementById('films');
  box.innerHTML = '';
  D.frames.forEach(function(f, k){
    const im = document.createElement('img');
    im.src = 'th/' + f.f + '/' + f.n;
    im.loading = 'lazy';
    im.onclick = function(){ show(k); };
    box.appendChild(im);
  });
}

function fit(){
  const st = document.getElementById('stage'), wr = document.getElementById('wrap');
  const r = D.frames[i].r || 16 / 9;
  let w = st.clientWidth - 16, h = w / r;
  if (h > st.clientHeight - 16){ h = st.clientHeight - 16; w = h * r; }
  wr.style.width = Math.round(w) + 'px';
  wr.style.height = Math.round(h) + 'px';
}

function show(k){
  i = Math.max(0, Math.min(D.frames.length - 1, k));
  const f = D.frames[i];
  document.getElementById('im').src = 'img/' + f.f + '/' + f.n;
  fit();
  document.getElementById('pos').textContent = (i + 1) + ' / ' + D.frames.length;
  const ims = document.getElementById('films').children;
  for (let j = 0; j < ims.length; j++) ims[j].className = (j === i ? 'on' : '');
  if (ims[i]) ims[i].scrollIntoView({block: 'nearest', inline: 'center'});
  draw();
  legend();
}

function draw(){
  const ov = document.getElementById('ov');
  ov.innerHTML = '';
  if (!showBox) return;
  D.frames[i].b.forEach(function(b){
    if (hidden.has(b[0])) return;
    const d = document.createElement('div');
    d.className = 'bx';
    d.style.borderColor = COLORS[b[0]];
    d.style.left = (b[1] * 100) + '%';
    d.style.top = (b[2] * 100) + '%';
    d.style.width = ((b[3] - b[1]) * 100) + '%';
    d.style.height = ((b[4] - b[2]) * 100) + '%';
    if (showLab){
      const s = document.createElement('span');
      s.className = 'lb';
      s.style.background = COLORS[b[0]];
      s.textContent = CLS[b[0]][0] + ' ' + CLS[b[0]][1];
      d.appendChild(s);
    }
    ov.appendChild(d);
  });
}

function legend(){
  const n = {};
  D.frames[i].b.forEach(function(b){ n[b[0]] = (n[b[0]] || 0) + 1; });
  const box = document.getElementById('legend');
  box.innerHTML = '';
  Object.keys(n).map(Number).sort(function(a, b){ return a - b; }).forEach(function(c){
    const row = document.createElement('div');
    row.className = 'cls' + (hidden.has(c) ? ' off' : '');
    row.onclick = function(){
      if (hidden.has(c)) hidden.delete(c); else hidden.add(c);
      draw(); legend();
    };
    row.innerHTML = '<span class="sw" style="background:' + COLORS[c] + '"></span>'
                  + '<span>' + CLS[c][0] + ' ' + CLS[c][1] + '</span>'
                  + '<span class="ct">' + n[c] + '</span>';
    box.appendChild(row);
  });
}

function go(d){ show(i + d); }
function toggleBox(){
  showBox = !showBox;
  document.getElementById('tb').className = showBox ? 'on' : '';
  draw();
}
function toggleLab(){
  showLab = !showLab;
  document.getElementById('tl').className = showLab ? 'on' : '';
  draw();
}
window.onresize = function(){ if (D) fit(); };
document.onkeydown = function(e){
  if (e.key === 'ArrowLeft') go(-1);
  else if (e.key === 'ArrowRight') go(1);
};
</script></body></html>
"""
