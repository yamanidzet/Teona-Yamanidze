// ─────────────────────────────────────────────────────────────────────────────
// MISATTRIBUTION MACHINE — p5.js Exhibition Sketch
// Exhibition: "What the Archive Forgot" — 12-screen LED installation
//
// Narrative without words:
//   1. PRISTINE      — Artwork appears whole, luminous
//   2. LABEL_APPLY   — An abstract 'stamp' descends — the wrong identity
//   3. CORRUPT       — The image fractures, shifts to wrong-identity palette
//   4. PROPAGATE     — Corrupted copies replicate across all screens
//   5. MACHINE_GAZE  — Three AI systems scan the work, confirm the error
//   6. INTERVENTION  — A research signal breaks through (the artist's truth)
//   7. TRUTH         — Image heals; correct identity colours flood the screens
//   8. FADE          — Cycle resets
// ─────────────────────────────────────────────────────────────────────────────

let state;
let artworkImages = {};      // { artistName: p5.Image }
let currentArtist;
let phaseIndex = 0;
let phaseStartTime = 0;
let particles = [];
let scanLines = [];
let archiveNodes = [];
let noiseOffset = 0;
let screenCfg;
let imageManifest = [];      // loaded from /api/images

// ── URL params ────────────────────────────────────────────────────────────────
// ?screen=N   (1-12)  which physical screen this browser is running on
// ?cols=4             columns in the grid (default 4)
// ?rows=3             rows in the grid (default 3)
// ?artist=Malevich    override artist rotation
// ?kiosk=1            visitor interaction kiosk mode
function getParam(name, fallback) {
  const u = new URLSearchParams(window.location.search);
  return u.has(name) ? u.get(name) : fallback;
}

// ── Setup ─────────────────────────────────────────────────────────────────────
function setup() {
  createCanvas(windowWidth, windowHeight);
  colorMode(HSB, 360, 100, 100, 100);
  textFont('monospace');

  screenCfg = {
    id:   int(getParam('screen', 1)),
    cols: int(getParam('cols',   4)),
    rows: int(getParam('rows',   3)),
    kiosk: getParam('kiosk', '0') === '1',
  };
  screenCfg.total = screenCfg.cols * screenCfg.rows;
  screenCfg.col   = (screenCfg.id - 1) % screenCfg.cols;
  screenCfg.row   = Math.floor((screenCfg.id - 1) / screenCfg.cols);

  // Logical full-canvas size (all screens together)
  screenCfg.fullW = width  * screenCfg.cols;
  screenCfg.fullH = height * screenCfg.rows;

  currentArtist = getParam('artist', 'Malevich');
  state = buildState(currentArtist);

  initParticles();
  initArchiveNodes();

  // Load image manifest from server (non-blocking)
  fetch('/api/images')
    .then(r => r.json())
    .then(data => {
      imageManifest = data.manifest || [];
      preloadArtworkImages();
    })
    .catch(() => {});  // server offline — proceed without images

  // Start sync
  if (typeof initSync === 'function') initSync();

  frameRate(60);
}

// ── Image preload ─────────────────────────────────────────────────────────────
function preloadArtworkImages() {
  // Load one representative open-access image per artist
  const artistFirst = {};
  for (const rec of imageManifest) {
    const a = rec.artist;
    if (!a || artworkImages[a]) continue;
    const url = rec.direct_url || rec.source_url;
    if (url && url.startsWith('http') && !artistFirst[a]) {
      artistFirst[a] = url;
    }
  }
  Object.entries(artistFirst).forEach(([artist, url]) => {
    loadImage(
      url,
      img => { artworkImages[artist] = img; },
      () => {}  // fail silently — glyph fallback used
    );
  });
}

// ── State builder ─────────────────────────────────────────────────────────────
function buildState(artistName) {
  const id = ARTWORK_IDENTITIES[artistName];
  return {
    artist:     artistName,
    identity:   id,
    phase:      PHASES.PRISTINE,
    phaseStart: millis(),
    corruptAmt: 0,
    truthAmt:   0,
    scannerY:   0,
    nodesActive: [],
  };
}

// ── Particles ─────────────────────────────────────────────────────────────────
function initParticles() {
  particles = [];
  for (let i = 0; i < 180; i++) {
    particles.push({
      x: random(width), y: random(height),
      vx: random(-0.4, 0.4), vy: random(-0.6, -0.1),
      size: random(2, 7),
      life: random(100),
      maxLife: random(80, 200),
      hue: random(200, 250),
    });
  }
}

// ── Archive propagation nodes ─────────────────────────────────────────────────
function initArchiveNodes() {
  archiveNodes = ARCHIVE_CHAIN.map((arc, i) => ({
    ...arc,
    x: map(i, 0, ARCHIVE_CHAIN.length - 1, width * 0.1, width * 0.9),
    y: map(arc.tier, 0, 3, height * 0.18, height * 0.82),
    activated: false,
    activatedAt: 0,
    pulse: 0,
  }));
}

// ── Phase management ──────────────────────────────────────────────────────────
function advancePhase() {
  phaseIndex = (phaseIndex + 1) % PHASE_ORDER.length;
  const nextPhase = Object.values(PHASES)[PHASE_ORDER[phaseIndex]];
  state.phase = nextPhase;
  state.phaseStart = millis();
  state.corruptAmt = (nextPhase.id >= PHASES.CORRUPT.id && nextPhase.id < PHASES.TRUTH.id) ? 1 : 0;

  if (nextPhase.id === PHASES.PRISTINE.id) {
    // Rotate artist
    const artists = Object.keys(ARTWORK_IDENTITIES);
    const idx = artists.indexOf(state.artist);
    currentArtist = artists[(idx + 1) % artists.length];
    state = buildState(currentArtist);
    phaseIndex = 0;
    initParticles();
    initArchiveNodes();
  }

  if (nextPhase.id === PHASES.PROPAGATE.id) {
    archiveNodes.forEach((n, i) => {
      n.activated = false;
      n.activatedAt = state.phaseStart + i * 600;
    });
  }
}

// ── Main draw ─────────────────────────────────────────────────────────────────
function draw() {
  const now = millis();
  const elapsed = now - state.phaseStart;
  const phaseDur = state.phase.duration;
  const t = constrain(elapsed / phaseDur, 0, 1);  // 0→1 within phase

  if (elapsed > phaseDur) advancePhase();

  // Translate so this screen renders its own viewport slice
  const ox = -screenCfg.col * width;
  const oy = -screenCfg.row * height;

  background(0, 0, 4);

  push();
  translate(ox, oy);
  drawFullCanvas(t, now);
  pop();

  // Per-screen local elements
  if (screenCfg.kiosk) drawKioskOverlay(t);
}

// ─────────────────────────────────────────────────────────────────────────────
// FULL-CANVAS drawing  (coordinate space = all screens together)
// ─────────────────────────────────────────────────────────────────────────────
function drawFullCanvas(t, now) {
  const id    = state.identity;
  const fw    = screenCfg.fullW;
  const fh    = screenCfg.fullH;
  const cx    = fw / 2;
  const cy    = fh / 2;
  const phase = state.phase.id;

  noiseOffset += 0.003;

  // ── 1. PRISTINE ──
  if (phase === PHASES.PRISTINE.id) {
    drawPristine(cx, cy, fw, fh, t, id);
  }

  // ── 2. LABEL_APPLY ──
  else if (phase === PHASES.LABEL_APPLY.id) {
    drawPristine(cx, cy, fw, fh, 1, id);
    drawLabelStamp(cx, cy, fw, fh, t, id);
  }

  // ── 3. CORRUPT ──
  else if (phase === PHASES.CORRUPT.id) {
    drawCorrupted(cx, cy, fw, fh, t, id, now);
  }

  // ── 4. PROPAGATE ──
  else if (phase === PHASES.PROPAGATE.id) {
    drawPropagation(cx, cy, fw, fh, t, id, now);
  }

  // ── 5. MACHINE_GAZE ──
  else if (phase === PHASES.MACHINE_GAZE.id) {
    drawMachineGaze(cx, cy, fw, fh, t, id, now);
  }

  // ── 6. INTERVENTION ──
  else if (phase === PHASES.INTERVENTION.id) {
    drawIntervention(cx, cy, fw, fh, t, id, now);
  }

  // ── 7. TRUTH ──
  else if (phase === PHASES.TRUTH.id) {
    drawTruth(cx, cy, fw, fh, t, id, now);
  }

  // ── 8. FADE ──
  else if (phase === PHASES.FADE.id) {
    drawTruth(cx, cy, fw, fh, 1, id, now);
    fill(0, 0, 0, map(t, 0, 1, 0, 100));
    noStroke();
    rect(0, 0, fw, fh);
  }

  // Grid lines (subtle) — always drawn
  drawGridOverlay(fw, fh);
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase visuals
// ─────────────────────────────────────────────────────────────────────────────

function drawPristine(cx, cy, fw, fh, t, id) {
  // Deep space background
  for (let y = 0; y < fh; y += 60) {
    const a = map(y, 0, fh, 8, 0);
    stroke(200, 30, 60, a);
    line(0, y, fw, y);
  }

  const r = min(fw, fh) * 0.28 * easeInOut(t);
  push();
  translate(cx, cy);

  // Use actual artwork image if loaded, otherwise glyph fallback
  const img = artworkImages[state.artist];
  if (img) {
    const imgSize = r * 2.2;
    // Soft vignette behind image
    for (let rr = imgSize * 0.7; rr > 0; rr -= 12) {
      const ch = hexToHSB(id.correct);
      fill(ch[0], ch[1] * 0.3, 15, map(rr, 0, imgSize * 0.7, 20, 0) * t);
      noStroke();
      ellipse(0, 0, rr * 2, rr * 1.8);
    }
    tint(255, 255 * t);
    imageMode(CENTER);
    image(img, 0, 0, imgSize, imgSize);
    noTint();
  } else {
    drawArtworkGlyph(r, id, t, false);
  }
  pop();

  // Floating identity fragments (correct colours)
  const fc = id.flag_colors;
  for (let i = 0; i < 12; i++) {
    const angle = TWO_PI * i / 12 + frameCount * 0.008;
    const rx = cos(angle) * (r * 1.6 + sin(frameCount * 0.02 + i) * 20);
    const ry = sin(angle) * (r * 1.4 + cos(frameCount * 0.03 + i) * 15);
    const c = hexToHSB(fc[i % fc.length]);
    fill(c[0], c[1], c[2], 55 * t);
    noStroke();
    const sz = 8 + 4 * sin(frameCount * 0.05 + i);
    ellipse(cx + rx, cy + ry, sz, sz);
  }

  // Ambient particles
  updateParticles(id.flag_colors, 0.6 * t);
}

function drawLabelStamp(cx, cy, fw, fh, t, id) {
  // Wrong-label stamp descends from above
  const stampY = lerp(-fh * 0.2, cy, easeInOut(t));
  const stampW = fw * 0.45;
  const stampH = fh * 0.22;

  push();
  translate(cx, stampY);

  // Stamp body — Soviet/imperial colour
  const wrongH = hexToHSB(id.flawed);
  fill(wrongH[0], wrongH[1], wrongH[2], 75);
  stroke(wrongH[0], wrongH[1], wrongH[2] - 10, 90);
  strokeWeight(3);
  rectMode(CENTER);
  rect(0, 0, stampW, stampH, 4);

  // Wrong-identity inner pattern (bars, not text)
  for (let i = -3; i <= 3; i++) {
    fill(wrongH[0], wrongH[1], max(wrongH[2]-25,0), 80);
    noStroke();
    rect(i * (stampW / 9), 0, stampW / 12, stampH * 0.6, 2);
  }

  // X mark on stamp
  stroke(0, 0, 100, 60);
  strokeWeight(4);
  const x2 = stampW * 0.12, y2 = stampH * 0.25;
  line(-x2, -y2, x2, y2);
  line(x2, -y2, -x2, y2);

  pop();

  // Impact ripples when stamp nears target
  if (t > 0.7) {
    const impact = map(t, 0.7, 1.0, 0, 1);
    for (let r = 1; r <= 5; r++) {
      const rr = r * 120 * impact;
      noFill();
      stroke(wrongH[0], 70, 80, max(0, 60 - r * 12) * impact);
      strokeWeight(2);
      ellipse(cx, cy, rr * 2, rr * 1.3);
    }
  }
}

function drawCorrupted(cx, cy, fw, fh, t, id, now) {
  // Glitch: artwork fractures; palette shifts to wrong-identity colors
  const wrongH = hexToHSB(id.flawed);
  const correctH = hexToHSB(id.correct);

  // Pixelation blocks
  const blockSize = lerp(2, 40, easeInOut(t));
  for (let x = 0; x < fw; x += blockSize) {
    for (let y = 0; y < fh; y += blockSize) {
      const n = noise(x / 200, y / 200, noiseOffset);
      if (n > 0.55) {
        const mixH = lerp(correctH[0], wrongH[0], t);
        fill(mixH, 70, map(n, 0.55, 1, 40, 90), 70);
        noStroke();
        rect(x, y, blockSize, blockSize);
      }
    }
  }

  // Central glyph — fragmenting
  push();
  translate(cx, cy);
  const r = min(fw, fh) * 0.28;
  drawArtworkGlyph(r, id, 1 - t * 0.5, true);

  // Shards breaking off
  for (let i = 0; i < 20; i++) {
    const angle = TWO_PI * i / 20 + now / 3000;
    const dist  = r * 0.8 + t * r * 0.7;
    const sx = cos(angle) * dist + random(-t * 30, t * 30);
    const sy = sin(angle) * dist + random(-t * 30, t * 30);
    fill(wrongH[0], 80, 70, 60 * (1 - t * 0.5));
    noStroke();
    push();
    translate(sx, sy);
    rotate(angle + t * PI);
    triangle(-8 * t, -5 * t, 8 * t, -5 * t, 0, 12 * t);
    pop();
  }
  pop();

  // Scan lines — visual noise
  for (let y = 0; y < fh; y += 8) {
    if (random() < 0.15 * t) {
      stroke(wrongH[0], 60, 80, 30);
      strokeWeight(1);
      line(0, y, fw, y);
    }
  }

  // Glitch horizontal bars
  for (let i = 0; i < 8 * t; i++) {
    const gy = random(fh);
    const gw = random(fw * 0.3, fw * 0.9);
    const gx = random(fw - gw);
    fill(wrongH[0], 90, 60, 25 * t);
    noStroke();
    rect(gx, gy, gw, random(2, 12));
  }
}

function drawPropagation(cx, cy, fw, fh, t, id, now) {
  const wrongH = hexToHSB(id.flawed);

  // Background stays corrupted
  drawCorrupted(cx, cy, fw, fh, 0.85, id, now);

  // Activate archive nodes over time
  archiveNodes.forEach(node => {
    if (!node.activated && now >= node.activatedAt) {
      node.activated = true;
    }
    if (node.activated) {
      node.pulse = (node.pulse + 0.05) % TWO_PI;
    }
  });

  // Draw archive connection lines (errors flowing downstream)
  for (let i = 0; i < archiveNodes.length - 1; i++) {
    const a = archiveNodes[i];
    const b = archiveNodes[i + 1];
    if (a.activated && b.activated) {
      const flowT = (now % 1800) / 1800;
      stroke(wrongH[0], 80, 70, 50);
      strokeWeight(1.5);
      line(a.x * (fw/width), a.y * (fh/height), b.x * (fw/width), b.y * (fh/height));

      // Animated dot flowing along line
      const fx = lerp(a.x, b.x, flowT) * (fw/width);
      const fy = lerp(a.y, b.y, flowT) * (fh/height);
      fill(wrongH[0], 90, 100, 80);
      noStroke();
      ellipse(fx, fy, 12, 12);
    }
  }

  // Draw archive nodes
  archiveNodes.forEach(node => {
    if (!node.activated) return;
    const nx = node.x * (fw/width);
    const ny = node.y * (fh/height);
    const pulse = sin(node.pulse) * 8;

    // Pulse ring
    noFill();
    stroke(wrongH[0], 70, 80, 40);
    strokeWeight(1.5);
    ellipse(nx, ny, 40 + pulse, 40 + pulse);

    // Node dot
    fill(wrongH[0], 80, 90, 90);
    noStroke();
    ellipse(nx, ny, 16 + pulse * 0.5, 16 + pulse * 0.5);

    // Icon for node type
    const iconH = node.type === 'llm' ? [200,80,90] : wrongH;
    fill(iconH[0], iconH[1], iconH[2], 70);
    noStroke();
    const iconSize = 6;
    if (node.type === 'llm') {
      // AI eye icon — triangle
      triangle(nx - iconSize, ny + iconSize/2, nx + iconSize, ny + iconSize/2, nx, ny - iconSize);
    } else {
      // Archive block
      rect(nx - iconSize/2, ny - iconSize/2, iconSize, iconSize);
    }
  });

  // Copies of the corrupted artwork appearing in corners
  const corners = [[fw*0.12, fh*0.14], [fw*0.88, fh*0.14], [fw*0.12, fh*0.86], [fw*0.88, fh*0.86]];
  corners.forEach(([bx, by], ci) => {
    if (t > ci * 0.2) {
      const copyT = constrain(map(t, ci * 0.2, ci * 0.2 + 0.25, 0, 1), 0, 1);
      push();
      translate(bx, by);
      const r = min(fw, fh) * 0.09;
      drawArtworkGlyph(r, id, 1, true);
      fill(wrongH[0], 70, 40, 30 * copyT);
      noStroke();
      ellipse(0, 0, r*2.4, r*2.4);
      pop();
    }
  });
}

function drawMachineGaze(cx, cy, fw, fh, t, id, now) {
  const wrongH = hexToHSB(id.flawed);
  drawCorrupted(cx, cy, fw, fh, 0.7, id, now);

  // Three AI scanning systems (visual only — no labels)
  const systems = [
    { hue: 200, speed: 0.8,  phaseOff: 0      }, // cloud LLM (blue)
    { hue: 140, speed: 1.1,  phaseOff: PI*0.6 }, // open-source LLM (green)
    { hue: 40,  speed: 0.6,  phaseOff: PI*1.3 }, // library catalog (amber)
  ];

  systems.forEach((sys, si) => {
    if (t < si * 0.25) return;
    const sysT = constrain(map(t, si * 0.25, si * 0.25 + 0.35, 0, 1), 0, 1);
    const scanY = (now / (1000 / sys.speed) + sys.phaseOff) % fh;

    // Horizontal scanner bar
    const scanH = lerp(2, fh * 0.08, sysT);
    noStroke();
    for (let dy = 0; dy < scanH; dy++) {
      const a = map(dy, 0, scanH, 50 * sysT, 0);
      fill(sys.hue, 90, 90, a);
      rect(0, (scanY + dy) % fh, fw, 1);
    }

    // Confidence circles around center — all wrong (red-tinted)
    const confR = min(fw, fh) * 0.4 * sysT;
    noFill();
    stroke(wrongH[0], 80, 70, 40 * sysT);
    strokeWeight(1.5);
    for (let r = 0; r < 4; r++) {
      ellipse(cx, cy, confR * (r / 3), confR * (r / 3) * 0.8);
    }

    // Wrong-answer confirmation burst (at peak scan)
    if (sysT > 0.8) {
      const burst = easeInOut(map(sysT, 0.8, 1.0, 0, 1));
      fill(wrongH[0], 90, 80, 60 * burst);
      noStroke();
      for (let i = 0; i < 8; i++) {
        const a = TWO_PI * i / 8 + si * 0.4;
        const bx = cx + cos(a) * confR * 0.6;
        const by = cy + sin(a) * confR * 0.5;
        ellipse(bx, by, 20 * burst, 20 * burst);
      }
    }
  });
}

function drawIntervention(cx, cy, fw, fh, t, id, now) {
  const correctH = hexToHSB(id.correct);
  const wrongH   = hexToHSB(id.flawed);

  // Corrupted background fading
  drawCorrupted(cx, cy, fw, fh, 1 - t * 0.8, id, now);

  // Intervention: a precise vertical beam cutting through
  const beamX = cx;
  const beamW = lerp(2, fw * 0.6, easeInOut(t));
  for (let bw = beamW; bw > 0; bw -= 8) {
    const a = map(bw, 0, beamW, 50, 0);
    fill(correctH[0], 60, 95, a);
    noStroke();
    rect(cx - bw / 2, 0, bw, fh);
  }

  // Central signal — correct-identity bloom
  const bloomR = min(fw, fh) * 0.25 * easeInOut(t);
  push();
  translate(cx, cy);
  for (let r = bloomR; r > 0; r -= 15) {
    const a = map(r, 0, bloomR, 60, 0);
    fill(correctH[0], 50, 100, a);
    noStroke();
    ellipse(0, 0, r * 2, r * 1.8);
  }

  // Correct glyph emerging
  drawArtworkGlyph(bloomR * 0.9, id, easeInOut(t), false);
  pop();

  // Shockwave rings from correction
  for (let r = 1; r <= 6; r++) {
    const rr = r * 80 + t * 200;
    if (rr < max(fw, fh)) {
      noFill();
      stroke(correctH[0], 70, 90, map(rr, 0, max(fw,fh)*0.8, 60, 0));
      strokeWeight(2);
      ellipse(cx, cy, rr * 2, rr * 1.6);
    }
  }
}

function drawTruth(cx, cy, fw, fh, t, id, now) {
  const correctH = hexToHSB(id.correct);
  const accentH  = hexToHSB(id.accent);
  const fc       = id.flag_colors.map(hexToHSB);

  // Flag-colour aurora wash across full canvas
  for (let y = 0; y < fh; y++) {
    const n = noise(y / 400, noiseOffset * 0.5);
    const ci = floor(n * fc.length);
    const c  = fc[ci];
    stroke(c[0], c[1] * 0.4, c[2] * 0.25, 15 * t);
    line(0, y, fw, y);
  }

  // Central restored artwork, enlarged
  const r = min(fw, fh) * 0.35 * easeInOut(t);
  push();
  translate(cx, cy);
  const img = artworkImages[state.artist];
  if (img) {
    // Image restored — sharper, larger, with correct-identity colour halo
    const ch = hexToHSB(id.correct);
    for (let rr = r * 1.3; rr > 0; rr -= 10) {
      fill(ch[0], 40, 80, map(rr, 0, r * 1.3, 35, 0) * t);
      noStroke();
      ellipse(0, 0, rr * 2, rr * 1.8);
    }
    tint(255, 255 * t);
    imageMode(CENTER);
    image(img, 0, 0, r * 2.2, r * 2.2);
    noTint();
  } else {
    drawArtworkGlyph(r, id, 1, false);
  }

  // Identity flag-colour petals radiating out
  for (let i = 0; i < 24; i++) {
    const angle  = TWO_PI * i / 24 + now / 8000;
    const pDist  = r * 1.25 + sin(now / 1200 + i) * 25;
    const pSize  = 18 + 8 * sin(now / 900 + i * 0.7);
    const fc2    = fc[i % fc.length];
    fill(fc2[0], fc2[1], fc2[2], 70 * t);
    noStroke();
    const px = cos(angle) * pDist;
    const py = sin(angle) * pDist * 0.85;
    push();
    translate(px, py);
    rotate(angle + PI / 2);
    ellipse(0, 0, pSize * 0.4, pSize);
    pop();
  }
  pop();

  // Constellation of satellite glyphs — correct-identity copies
  const satCount = 6;
  for (let i = 0; i < satCount; i++) {
    const angle  = TWO_PI * i / satCount + now / 12000 + PI / 6;
    const satR   = min(fw, fh) * 0.4;
    const bx     = cx + cos(angle) * satR;
    const by     = cy + sin(angle) * satR * 0.7;
    const satSize = r * 0.3;

    if (t > i / satCount * 0.6) {
      const satT = constrain(map(t, i / satCount * 0.6, i / satCount * 0.6 + 0.3, 0, 1), 0, 1);
      push();
      translate(bx, by);
      drawArtworkGlyph(satSize * easeInOut(satT), id, 1, false);
      pop();

      // Connection line to center
      stroke(correctH[0], 50, 80, 20 * satT);
      strokeWeight(1);
      line(cx, cy, bx, by);
    }
  }

  // Flowing particles in correct-identity colours
  updateParticles(id.flag_colors, t);
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared: Artwork Identity Glyph
// ─────────────────────────────────────────────────────────────────────────────
function drawArtworkGlyph(r, id, t, corrupted) {
  const ch = hexToHSB(corrupted ? id.flawed : id.correct);
  const ah = hexToHSB(id.accent);

  // Outer ring
  noFill();
  stroke(ch[0], ch[1], ch[2], 80 * t);
  strokeWeight(2);
  ellipse(0, 0, r * 2, r * 2);

  // Inner geometric — unique per artist
  const a = state.artist;

  if (a === 'Malevich') {
    // Suprematist composition — squares and rectangles
    fill(ch[0], 80, 70, 75 * t);
    noStroke();
    rect(-r * 0.38, -r * 0.38, r * 0.76, r * 0.76);
    fill(ah[0], ah[1], ah[2], 85 * t);
    rect(-r * 0.18, r * 0.12, r * 0.55, r * 0.24);
    fill(ch[0], 40, 90, 60 * t);
    rect(-r * 0.5, -r * 0.1, r * 0.22, r * 0.5);

  } else if (a === 'Exter') {
    // Cubo-Futurist — faceted planes
    fill(ch[0], 70, 80, 75 * t);
    noStroke();
    for (let i = 0; i < 6; i++) {
      const ang = TWO_PI * i / 6 + PI / 6;
      const nx  = cos(ang) * r * 0.55;
      const ny  = sin(ang) * r * 0.55;
      const ang2 = TWO_PI * ((i + 1) % 6) / 6 + PI / 6;
      fill(ch[0], 60 + i * 4, 70 + i * 3, 65 * t);
      triangle(0, 0, nx, ny, cos(ang2) * r * 0.55, sin(ang2) * r * 0.55);
    }
    fill(ah[0], ah[1], ah[2], 80 * t);
    ellipse(0, 0, r * 0.35, r * 0.35);

  } else if (a === 'Pagava') {
    // Lyrical abstraction — organic curves
    fill(ch[0], 50, 75, 70 * t);
    noStroke();
    beginShape();
    for (let ang = 0; ang < TWO_PI; ang += 0.2) {
      const nr = r * 0.55 * (1 + 0.25 * sin(ang * 3 + noiseOffset * 2));
      vertex(cos(ang) * nr, sin(ang) * nr);
    }
    endShape(CLOSE);
    fill(ah[0], ah[1], 80, 70 * t);
    ellipse(0, -r * 0.15, r * 0.25, r * 0.35);

  } else if (a === 'Kakabadze') {
    // Constructivist sails — overlapping angular planes
    fill(ch[0], 75, 70, 70 * t);
    noStroke();
    triangle(-r * 0.5, r * 0.45, 0, -r * 0.5, r * 0.45, r * 0.1);
    fill(ah[0], ah[1], ah[2], 65 * t);
    triangle(-r * 0.15, r * 0.5, r * 0.5, r * 0.15, r * 0.3, -r * 0.45);
    fill(ch[0], 40, 90, 50 * t);
    ellipse(-r * 0.15, -r * 0.15, r * 0.4, r * 0.4);

  } else if (a === 'Parajanov') {
    // Pomegranate / mosaic — radial pattern
    for (let i = 0; i < 12; i++) {
      const ang = TWO_PI * i / 12;
      const ang2 = TWO_PI * (i + 1) / 12;
      const ri = r * 0.55;
      const cf = hexToHSB(id.flag_colors[i % id.flag_colors.length]);
      fill(cf[0], cf[1], cf[2], 70 * t);
      noStroke();
      arc(0, 0, ri * 2, ri * 2, ang, ang2, PIE);
    }
    fill(0, 0, 20, 80 * t);
    noStroke();
    ellipse(0, 0, r * 0.22, r * 0.22);
  }

  // If corrupted: overlaid glitch bars
  if (corrupted) {
    const wh = hexToHSB(id.flawed);
    for (let i = 0; i < 6; i++) {
      const gy = random(-r, r);
      fill(wh[0], 80, 70, 40);
      noStroke();
      rect(-r, gy, r * 2, random(2, 8));
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Particles
// ─────────────────────────────────────────────────────────────────────────────
function updateParticles(flagColors, alpha) {
  const fw = screenCfg.fullW;
  const fh = screenCfg.fullH;

  particles.forEach(p => {
    p.x += p.vx + sin(frameCount * 0.02 + p.y / 100) * 0.3;
    p.y += p.vy;
    p.life++;
    if (p.life > p.maxLife || p.y < 0 || p.x < 0 || p.x > fw) {
      p.x = random(fw);
      p.y = fh + p.size;
      p.vy = random(-0.8, -0.2);
      p.vx = random(-0.4, 0.4);
      p.life = 0;
    }
    const lifeRatio = 1 - p.life / p.maxLife;
    const fc = hexToHSB(flagColors[floor(p.x / fw * flagColors.length) % flagColors.length]);
    fill(fc[0], fc[1], fc[2], 70 * lifeRatio * alpha);
    noStroke();
    ellipse(p.x, p.y, p.size * lifeRatio, p.size * lifeRatio);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Grid overlay (screen boundaries for multi-screen alignment)
// ─────────────────────────────────────────────────────────────────────────────
function drawGridOverlay(fw, fh) {
  stroke(200, 20, 40, 15);
  strokeWeight(1);
  for (let c = 1; c < screenCfg.cols; c++) {
    const x = c * (fw / screenCfg.cols);
    line(x, 0, x, fh);
  }
  for (let r = 1; r < screenCfg.rows; r++) {
    const y = r * (fh / screenCfg.rows);
    line(0, y, fw, y);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Kiosk overlay (visitor interaction screen)
// ─────────────────────────────────────────────────────────────────────────────
function drawKioskOverlay(t) {
  // Subtle pulse indicator at bottom — invites touch/interaction
  const pulseSize = 40 + 12 * sin(frameCount * 0.08);
  const id = state.identity;
  const ch = hexToHSB(id.correct);
  fill(ch[0], 70, 90, 50 * (0.5 + 0.5 * sin(frameCount * 0.06)));
  noStroke();
  ellipse(width / 2, height - 60, pulseSize, pulseSize);

  // Three dots  =  "tap to query AI"
  for (let i = -1; i <= 1; i++) {
    fill(ch[0], 60, 95, 70);
    ellipse(width / 2 + i * 18, height - 60, 8, 8);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────
function hexToHSB(hex) {
  // Returns [h, s, b] in p5 HSB(360,100,100) space
  const r = parseInt(hex.slice(1,3),16)/255;
  const g = parseInt(hex.slice(3,5),16)/255;
  const b = parseInt(hex.slice(5,7),16)/255;
  const max = Math.max(r,g,b), min = Math.min(r,g,b);
  const d = max - min;
  let h = 0;
  if (d > 0) {
    if      (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else                h = (r - g) / d + 4;
    h = h * 60;
    if (h < 0) h += 360;
  }
  const s = max === 0 ? 0 : d / max;
  return [h, s * 100, max * 100];
}

function easeInOut(t) {
  return t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  screenCfg.fullW = width  * screenCfg.cols;
  screenCfg.fullH = height * screenCfg.rows;
  initArchiveNodes();
}
