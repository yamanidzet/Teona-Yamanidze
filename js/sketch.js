// ─────────────────────────────────────────────────────────────────────────────
// MISATTRIBUTION MACHINE — p5.js Exhibition Sketch
// Exhibition: "What the Archive Forgot" — 12-screen LED installation
//
// Visual language: distortion = misattribution. Clarity = truth.
// No colour coding. Neutral palette throughout.
//
// Phases:
//   1. PRISTINE      — Artwork clear and whole
//   2. LABEL_APPLY   — A mark descends and settles on the image
//   3. CORRUPT       — Fragmentation, pixelation, glitch, noise
//   4. PROPAGATE     — Distorted copies replicate across all screens
//   5. MACHINE_GAZE  — Three systems scan the corrupted image
//   6. INTERVENTION  — A precise signal cuts through the noise
//   7. TRUTH         — Image becomes fully clear and whole again
//   8. FADE          — Cycle resets
// ─────────────────────────────────────────────────────────────────────────────

let state;
let artworkImages = {};
let currentArtist;
let phaseIndex  = 0;
let particles   = [];
let archiveNodes = [];
let noiseOffset  = 0;
let screenCfg;
let imageManifest = [];

// ── URL params ────────────────────────────────────────────────────────────────
function getParam(name, fallback) {
  const u = new URLSearchParams(window.location.search);
  return u.has(name) ? u.get(name) : fallback;
}

// ── Setup ─────────────────────────────────────────────────────────────────────
function setup() {
  createCanvas(windowWidth, windowHeight);
  colorMode(HSB, 360, 100, 100, 100);

  screenCfg = {
    id:   int(getParam('screen', 1)),
    cols: int(getParam('cols',   4)),
    rows: int(getParam('rows',   3)),
    kiosk: getParam('kiosk', '0') === '1',
  };
  screenCfg.total = screenCfg.cols * screenCfg.rows;
  screenCfg.col   = (screenCfg.id - 1) % screenCfg.cols;
  screenCfg.row   = Math.floor((screenCfg.id - 1) / screenCfg.cols);
  screenCfg.fullW = width  * screenCfg.cols;
  screenCfg.fullH = height * screenCfg.rows;

  currentArtist = getParam('artist', 'Malevich');
  state = buildState(currentArtist);

  initParticles();
  initArchiveNodes();

  fetch('/api/images')
    .then(r => r.json())
    .then(data => { imageManifest = data.manifest || []; preloadArtworkImages(); })
    .catch(() => {});

  if (typeof initSync === 'function') initSync();
  frameRate(60);
}

// ── Image preload ─────────────────────────────────────────────────────────────
function preloadArtworkImages() {
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
    loadImage(url, img => { artworkImages[artist] = img; }, () => {});
  });
}

// ── State builder ─────────────────────────────────────────────────────────────
function buildState(artistName) {
  return {
    artist:     artistName,
    identity:   ARTWORK_IDENTITIES[artistName],
    phase:      PHASES.PRISTINE,
    phaseStart: millis(),
  };
}

// ── Particles (neutral — light dust) ─────────────────────────────────────────
function initParticles() {
  particles = [];
  for (let i = 0; i < 120; i++) {
    particles.push({
      x: random(screenCfg.fullW || width),
      y: random(screenCfg.fullH || height),
      vx: random(-0.2, 0.2),
      vy: random(-0.4, -0.05),
      size: random(1, 4),
      life: random(100),
      maxLife: random(100, 240),
    });
  }
}

// ── Archive nodes ─────────────────────────────────────────────────────────────
function initArchiveNodes() {
  archiveNodes = ARCHIVE_CHAIN.map((arc, i) => ({
    ...arc,
    x: map(i, 0, ARCHIVE_CHAIN.length - 1, 0.1, 0.9),
    y: map(arc.tier, 0, 3, 0.15, 0.82),
    activated: false,
    activatedAt: 0,
    pulse: random(TWO_PI),
  }));
}

// ── Phase management ──────────────────────────────────────────────────────────
function advancePhase() {
  phaseIndex = (phaseIndex + 1) % PHASE_ORDER.length;
  const phases = Object.values(PHASES);
  const next   = phases[PHASE_ORDER[phaseIndex]];
  state.phase      = next;
  state.phaseStart = millis();

  if (next.id === PHASES.PRISTINE.id) {
    const artists = Object.keys(ARTWORK_IDENTITIES);
    const idx = artists.indexOf(state.artist);
    currentArtist = artists[(idx + 1) % artists.length];
    state = buildState(currentArtist);
    phaseIndex = 0;
    initParticles();
    initArchiveNodes();
  }

  if (next.id === PHASES.PROPAGATE.id) {
    archiveNodes.forEach((n, i) => {
      n.activated   = false;
      n.activatedAt = state.phaseStart + i * 650;
    });
  }
}

// ── Main draw ─────────────────────────────────────────────────────────────────
function draw() {
  const now     = millis();
  const elapsed = now - state.phaseStart;
  const t       = constrain(elapsed / state.phase.duration, 0, 1);

  if (elapsed > state.phase.duration) advancePhase();

  const ox = -screenCfg.col * width;
  const oy = -screenCfg.row * height;

  background(0, 0, 3);

  push();
  translate(ox, oy);
  drawFullCanvas(t, now);
  pop();
}

// ─────────────────────────────────────────────────────────────────────────────
// FULL CANVAS
// ─────────────────────────────────────────────────────────────────────────────
function drawFullCanvas(t, now) {
  const fw  = screenCfg.fullW;
  const fh  = screenCfg.fullH;
  const cx  = fw / 2;
  const cy  = fh / 2;
  const pid = state.phase.id;

  noiseOffset += 0.002;

  if      (pid === PHASES.PRISTINE.id)     drawPristine    (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.LABEL_APPLY.id)  drawLabelApply  (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.CORRUPT.id)      drawCorrupt     (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.PROPAGATE.id)    drawPropagate   (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.MACHINE_GAZE.id) drawMachineGaze (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.INTERVENTION.id) drawIntervention(cx, cy, fw, fh, t, now);
  else if (pid === PHASES.TRUTH.id)        drawTruth       (cx, cy, fw, fh, t, now);
  else if (pid === PHASES.FADE.id) {
    drawTruth(cx, cy, fw, fh, 1, now);
    noStroke();
    fill(0, 0, 0, map(t, 0, 1, 0, 100));
    rect(0, 0, fw, fh);
  }

  drawScreenGrid(fw, fh);
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. PRISTINE — image appears clean and whole, gently luminous
// ─────────────────────────────────────────────────────────────────────────────
function drawPristine(cx, cy, fw, fh, t, now) {
  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.52 * easeInOut(t);

  push();
  translate(cx, cy);

  // Soft glow behind image
  for (let r = size * 0.8; r > 0; r -= 18) {
    fill(0, 0, 100, map(r, 0, size * 0.8, 6, 0) * t);
    noStroke();
    ellipse(0, 0, r * 2, r * 2);
  }

  if (img) {
    tint(0, 0, 100, 95 * t);
    imageMode(CENTER);
    image(img, 0, 0, size, size);
    noTint();
  } else {
    drawGlyph(size * 0.5, t, 0);
  }
  pop();

  // Quiet floating dust — barely visible
  drawDust(0.25 * t, fw, fh);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. LABEL APPLY — a geometric mark settles onto the image
// ─────────────────────────────────────────────────────────────────────────────
function drawLabelApply(cx, cy, fw, fh, t, now) {
  // Image underneath, still clear
  drawPristine(cx, cy, fw, fh, 1, now);

  // Rectangular mark descends from top
  const markW  = fw * 0.42;
  const markH  = fh * 0.18;
  const markY  = lerp(-fh * 0.15, cy, easeInOut(t));
  const markA  = 70 * easeInOut(t);

  push();
  translate(cx, markY);
  rectMode(CENTER);

  // Outer border — dark, heavy
  noFill();
  stroke(0, 0, 85, markA * 0.6);
  strokeWeight(2);
  rect(0, 0, markW, markH);

  // Inner fill — dark grey, semi-opaque
  fill(0, 0, 8, markA * 0.85);
  noStroke();
  rect(0, 0, markW - 4, markH - 4);

  // Horizontal bars inside (abstract label structure, no text)
  for (let i = -2; i <= 2; i++) {
    const barW = markW * (i === 0 ? 0.55 : 0.3);
    fill(0, 0, 70, 40 * easeInOut(t));
    noStroke();
    rect(i * (markW / 6), i * (markH / 7), barW, markH * 0.06, 1);
  }

  // Impact — image begins to respond when stamp lands
  if (t > 0.75) {
    const impact = easeInOut(map(t, 0.75, 1.0, 0, 1));
    for (let r = 1; r <= 4; r++) {
      const rr = r * 90 * impact;
      noFill();
      stroke(0, 0, 80, max(0, 35 - r * 8) * impact);
      strokeWeight(1);
      ellipse(0, cy - markY, rr * 2, rr * 1.4);
    }
  }
  pop();
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. CORRUPT — fragmentation, pixelation, glitch
// ─────────────────────────────────────────────────────────────────────────────
function drawCorrupt(cx, cy, fw, fh, t, now) {
  const img    = artworkImages[state.artist];
  const size   = min(fw, fh) * 0.52;

  // ── Pixel dissolution ──
  const blockSize = lerp(2, 48, easeInOut(t));
  for (let x = cx - size * 0.6; x < cx + size * 0.6; x += blockSize) {
    for (let y = cy - size * 0.6; y < cy + size * 0.6; y += blockSize) {
      const n = noise(x / 180, y / 180, noiseOffset);
      if (n > lerp(0.72, 0.38, t)) {
        const bri = random(10, 55);
        fill(0, 0, bri, 65);
        noStroke();
        rect(x, y, blockSize, blockSize);
      }
    }
  }

  // ── Underlying image, fading and shifting ──
  push();
  translate(cx, cy);
  if (img) {
    // Image drifts and dims
    const drift = t * 8;
    tint(0, 0, 100, map(t, 0, 1, 90, 20));
    imageMode(CENTER);
    image(img, random(-drift, drift), random(-drift, drift), size, size);
    noTint();
  } else {
    drawGlyph(size * 0.5, 1 - t * 0.6, t);
  }

  // Breaking shards
  for (let i = 0; i < int(20 * t); i++) {
    const angle  = random(TWO_PI);
    const dist   = random(size * 0.2, size * 0.65);
    const sx     = cos(angle) * dist;
    const sy     = sin(angle) * dist;
    const shardW = random(4, 22) * t;
    const shardH = random(2, 10) * t;
    fill(0, 0, random(15, 65), 55);
    noStroke();
    push();
    translate(sx, sy);
    rotate(angle + t * PI * random(-1, 1));
    rect(-shardW / 2, -shardH / 2, shardW, shardH);
    pop();
  }
  pop();

  // ── Horizontal glitch bars ──
  for (let i = 0; i < 12 * t; i++) {
    const gy  = random(fh);
    const gw  = random(fw * 0.15, fw * 0.85);
    const gx  = random(fw - gw);
    const bri = random(5, 40);
    fill(0, 0, bri, 30 * t);
    noStroke();
    rect(gx, gy, gw, random(1, 9));
  }

  // ── Vertical tears ──
  if (t > 0.5) {
    for (let i = 0; i < 4; i++) {
      const tx   = random(fw);
      const th   = random(fh * 0.1, fh * 0.5);
      const ty   = random(fh - th);
      const bri  = random(20, 50);
      fill(0, 0, bri, 20 * (t - 0.5) * 2);
      noStroke();
      rect(tx, ty, random(1, 5), th);
    }
  }

  // ── Scan line overlay ──
  for (let y = 0; y < fh; y += 6) {
    stroke(0, 0, 0, 18);
    strokeWeight(1);
    line(0, y, fw, y);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. PROPAGATE — distorted copies replicate across the grid
// ─────────────────────────────────────────────────────────────────────────────
function drawPropagate(cx, cy, fw, fh, t, now) {
  // Background stays corrupted
  drawCorrupt(cx, cy, fw, fh, 0.88, now);

  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.14;

  // Activate archive nodes
  archiveNodes.forEach(node => {
    if (!node.activated && now >= node.activatedAt) node.activated = true;
    if (node.activated) node.pulse = (node.pulse + 0.04) % TWO_PI;
  });

  // Connection lines
  for (let i = 0; i < archiveNodes.length - 1; i++) {
    const a = archiveNodes[i];
    const b = archiveNodes[i + 1];
    if (!a.activated || !b.activated) continue;
    const ax = a.x * fw, ay = a.y * fh;
    const bx = b.x * fw, by = b.y * fh;
    stroke(0, 0, 55, 35);
    strokeWeight(1);
    line(ax, ay, bx, by);
    // Animated signal dot
    const ft = (now % 1600) / 1600;
    fill(0, 0, 90, 80);
    noStroke();
    ellipse(lerp(ax, bx, ft), lerp(ay, by, ft), 8, 8);
  }

  // Nodes
  archiveNodes.forEach(node => {
    if (!node.activated) return;
    const nx = node.x * fw;
    const ny = node.y * fh;
    const ps = sin(node.pulse) * 6;
    noFill();
    stroke(0, 0, 60, 35);
    strokeWeight(1);
    ellipse(nx, ny, 36 + ps, 36 + ps);
    fill(0, 0, 75, 85);
    noStroke();
    ellipse(nx, ny, 12 + ps * 0.4, 12 + ps * 0.4);
  });

  // Corrupted copies at corners — appearing one by one
  const positions = [
    [fw * 0.11, fh * 0.13],
    [fw * 0.89, fh * 0.13],
    [fw * 0.11, fh * 0.87],
    [fw * 0.89, fh * 0.87],
    [fw * 0.50, fh * 0.10],
    [fw * 0.50, fh * 0.90],
  ];
  positions.forEach(([bx, by], i) => {
    const threshold = i * 0.14;
    if (t < threshold) return;
    const copyT = constrain(map(t, threshold, threshold + 0.18, 0, 1), 0, 1);
    push();
    translate(bx, by);
    if (img) {
      tint(0, 0, 100, 40 * copyT);
      imageMode(CENTER);
      image(img, 0, 0, size * 2, size * 2);
      noTint();
      // Glitch overlay on copy
      for (let g = 0; g < 3; g++) {
        fill(0, 0, random(10, 50), 35 * copyT);
        noStroke();
        rect(-size + random(size * 2), -size * random(0.5), random(size * 0.8, size * 1.6), random(3, 12));
      }
    } else {
      drawGlyph(size * 0.7, copyT, 0.6);
    }
    pop();
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. MACHINE GAZE — three systems scan the corrupted image
// ─────────────────────────────────────────────────────────────────────────────
function drawMachineGaze(cx, cy, fw, fh, t, now) {
  drawCorrupt(cx, cy, fw, fh, 0.75, now);

  const scanSystems = [
    { speed: 700,  offset: 0,          brightness: 85 },
    { speed: 1050, offset: fh * 0.33,  brightness: 60 },
    { speed: 850,  offset: fh * 0.67,  brightness: 75 },
  ];

  scanSystems.forEach((sys, si) => {
    if (t < si * 0.22) return;
    const sysT  = constrain(map(t, si * 0.22, si * 0.22 + 0.35, 0, 1), 0, 1);
    const scanY = ((now / sys.speed * fh) + sys.offset) % fh;
    const barH  = lerp(1, fh * 0.06, sysT);

    // Scan bar — bright leading edge, fading trail
    noStroke();
    for (let dy = 0; dy < barH; dy++) {
      const a = map(dy, 0, barH, 28 * sysT, 0);
      fill(0, 0, sys.brightness, a);
      rect(0, (scanY + dy) % fh, fw, 1);
    }

    // Leading edge line
    stroke(0, 0, sys.brightness, 50 * sysT);
    strokeWeight(1);
    line(0, scanY % fh, fw, scanY % fh);

    // Targeting reticle at centre
    if (sysT > 0.5) {
      const rl  = min(fw, fh) * 0.22 * easeInOut(map(sysT, 0.5, 1.0, 0, 1));
      const gap = rl * 0.28;
      noFill();
      stroke(0, 0, sys.brightness, 40 * sysT);
      strokeWeight(1);
      // Corner marks only — not a full circle
      for (let q = 0; q < 4; q++) {
        const qx = (q < 2 ? -1 : 1) * rl;
        const qy = (q % 2 === 0 ? -1 : 1) * rl;
        const ex = (q < 2 ? -1 : 1) * gap;
        const ey = (q % 2 === 0 ? -1 : 1) * gap;
        line(cx + qx, cy + qy, cx + qx, cy + ey);
        line(cx + qx, cy + qy, cx + ex, cy + qy);
      }
    }
  });

  // At peak — all three confirm wrong answer — brief flicker
  if (t > 0.85) {
    const flicker = sin(now / 60) * 0.5 + 0.5;
    fill(0, 0, 0, 25 * flicker * (t - 0.85) / 0.15);
    noStroke();
    rect(0, 0, fw, fh);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. INTERVENTION — a clean signal cuts through
// ─────────────────────────────────────────────────────────────────────────────
function drawIntervention(cx, cy, fw, fh, t, now) {
  // Distortion fades as correction enters
  drawCorrupt(cx, cy, fw, fh, 1 - t * 0.9, now);

  const beamW = lerp(1, fw * 0.55, easeInOut(t));

  // Vertical beam — pure white, expanding
  for (let bw = beamW; bw > 0; bw -= 10) {
    fill(0, 0, 100, map(bw, 0, beamW, 22, 0));
    noStroke();
    rect(cx - bw / 2, 0, bw, fh);
  }
  // Bright core line
  stroke(0, 0, 100, 60 * easeInOut(t));
  strokeWeight(1.5);
  line(cx, 0, cx, fh);

  // Image re-emerging at centre
  const img    = artworkImages[state.artist];
  const emerge = easeInOut(t);
  push();
  translate(cx, cy);
  if (img) {
    tint(0, 0, 100, 85 * emerge);
    imageMode(CENTER);
    const sz = min(fw, fh) * 0.52 * emerge;
    image(img, 0, 0, sz, sz);
    noTint();
  } else {
    drawGlyph(min(fw, fh) * 0.25 * emerge, emerge, 0);
  }
  pop();

  // Expanding rings from centre
  for (let r = 1; r <= 5; r++) {
    const rr = r * 100 + t * 180;
    if (rr > max(fw, fh) * 0.7) continue;
    noFill();
    stroke(0, 0, 100, map(rr, 0, max(fw, fh) * 0.7, 30, 0) * easeInOut(t));
    strokeWeight(1);
    ellipse(cx, cy, rr * 2, rr * 1.6);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. TRUTH — image is fully clear, whole, luminous. No distortion.
// ─────────────────────────────────────────────────────────────────────────────
function drawTruth(cx, cy, fw, fh, t, now) {
  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.52;

  // Clean light wash — very subtle
  for (let y = 0; y < fh; y += 4) {
    const n = noise(y / 600, noiseOffset * 0.3);
    stroke(0, 0, 100, n * 4 * t);
    line(0, y, fw, y);
  }

  // Central image — clear, sharp, whole
  push();
  translate(cx, cy);

  // Gentle white halo
  for (let r = size * 0.65; r > 0; r -= 20) {
    fill(0, 0, 100, map(r, 0, size * 0.65, 9, 0) * t);
    noStroke();
    ellipse(0, 0, r * 2, r * 2);
  }

  if (img) {
    tint(0, 0, 100, 97 * t);
    imageMode(CENTER);
    image(img, 0, 0, size * easeInOut(t), size * easeInOut(t));
    noTint();
  } else {
    drawGlyph(size * 0.5 * easeInOut(t), 1, 0);
  }
  pop();

  // Orbiting smaller instances — the work existing in multiple places, correctly
  const satCount = 5;
  for (let i = 0; i < satCount; i++) {
    const threshold = i * 0.15;
    if (t < threshold) continue;
    const satT  = constrain(map(t, threshold, threshold + 0.25, 0, 1), 0, 1);
    const angle = TWO_PI * i / satCount + now / 14000;
    const orb   = min(fw, fh) * 0.42;
    const bx    = cx + cos(angle) * orb;
    const by    = cy + sin(angle) * orb * 0.7;
    const sz    = size * 0.22 * easeInOut(satT);

    // Thin connection to centre
    stroke(0, 0, 90, 12 * satT);
    strokeWeight(1);
    line(cx, cy, bx, by);

    push();
    translate(bx, by);
    if (img) {
      tint(0, 0, 100, 70 * satT);
      imageMode(CENTER);
      image(img, 0, 0, sz, sz);
      noTint();
    } else {
      drawGlyph(sz * 0.5, satT, 0);
    }
    pop();
  }

  // Fine dust — settled, calm
  drawDust(0.4 * t, fw, fh);
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared glyph (fallback when no image loaded)
// ─────────────────────────────────────────────────────────────────────────────
function drawGlyph(r, alpha, corruptAmt) {
  const a = state.artist;

  if (corruptAmt > 0) {
    // Corrupted: broken, irregular
    for (let i = 0; i < 8; i++) {
      const angle = TWO_PI * i / 8 + corruptAmt * random(-0.3, 0.3);
      const dist  = r * random(0.4, 1.0);
      fill(0, 0, random(20, 60), 55 * alpha);
      noStroke();
      push();
      translate(cos(angle) * dist, sin(angle) * dist);
      rotate(random(TWO_PI));
      rect(-r * 0.12, -r * 0.04, r * 0.24, r * 0.08);
      pop();
    }
    return;
  }

  fill(0, 0, 80, 80 * alpha);
  noStroke();

  if (a === 'Malevich') {
    // Suprematist — squares
    rectMode(CENTER);
    rect(0, 0, r * 0.9, r * 0.9);
    fill(0, 0, 40, 80 * alpha);
    rect(r * 0.18, r * 0.18, r * 0.45, r * 0.18);
    fill(0, 0, 95, 70 * alpha);
    rect(-r * 0.3, -r * 0.05, r * 0.16, r * 0.55);

  } else if (a === 'Exter') {
    // Cubo-Futurist — faceted
    for (let i = 0; i < 6; i++) {
      const ang  = TWO_PI * i / 6 + PI / 6;
      const ang2 = TWO_PI * ((i + 1) % 6) / 6 + PI / 6;
      fill(0, 0, map(i, 0, 5, 30, 85), 70 * alpha);
      triangle(0, 0,
        cos(ang)  * r * 0.55, sin(ang)  * r * 0.55,
        cos(ang2) * r * 0.55, sin(ang2) * r * 0.55);
    }

  } else if (a === 'Pagava') {
    // Lyrical — organic
    beginShape();
    for (let ang = 0; ang < TWO_PI; ang += 0.18) {
      const nr = r * 0.52 * (1 + 0.22 * sin(ang * 3 + noiseOffset * 2));
      vertex(cos(ang) * nr, sin(ang) * nr);
    }
    endShape(CLOSE);
    fill(0, 0, 30, 70 * alpha);
    ellipse(0, -r * 0.12, r * 0.22, r * 0.32);

  } else if (a === 'Kakabadze') {
    // Constructivist sails
    triangle(-r * 0.5, r * 0.44, 0, -r * 0.5, r * 0.44, r * 0.1);
    fill(0, 0, 45, 65 * alpha);
    triangle(-r * 0.12, r * 0.5, r * 0.5, r * 0.12, r * 0.28, -r * 0.44);
    fill(0, 0, 92, 55 * alpha);
    ellipse(-r * 0.14, -r * 0.14, r * 0.38, r * 0.38);

  } else if (a === 'Parajanov') {
    // Radial mosaic
    for (let i = 0; i < 12; i++) {
      const ang  = TWO_PI * i / 12;
      const ang2 = TWO_PI * (i + 1) / 12;
      fill(0, 0, map(i % 3, 0, 2, 25, 85), 70 * alpha);
      arc(0, 0, r * 1.1, r * 1.1, ang, ang2, PIE);
    }
    fill(0, 0, 6, 85 * alpha);
    ellipse(0, 0, r * 0.2, r * 0.2);
  }

  noStroke();
  fill(0, 0, 100, 70 * alpha);
  ellipse(0, 0, r * 0.08, r * 0.08);
}

// ─────────────────────────────────────────────────────────────────────────────
// Dust particles — neutral
// ─────────────────────────────────────────────────────────────────────────────
function drawDust(alpha, fw, fh) {
  noStroke();
  particles.forEach(p => {
    p.x += p.vx;
    p.y += p.vy;
    p.life++;
    if (p.life > p.maxLife || p.y < 0 || p.x < 0 || p.x > fw) {
      p.x = random(fw); p.y = fh + p.size;
      p.vy = random(-0.4, -0.08); p.vx = random(-0.2, 0.2); p.life = 0;
    }
    const lr = 1 - p.life / p.maxLife;
    fill(0, 0, 88, 55 * lr * alpha);
    ellipse(p.x, p.y, p.size * lr, p.size * lr);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Screen grid — faint lines marking panel boundaries
// ─────────────────────────────────────────────────────────────────────────────
function drawScreenGrid(fw, fh) {
  stroke(0, 0, 100, 8);
  strokeWeight(1);
  for (let c = 1; c < screenCfg.cols; c++) {
    line(c * (fw / screenCfg.cols), 0, c * (fw / screenCfg.cols), fh);
  }
  for (let r = 1; r < screenCfg.rows; r++) {
    line(0, r * (fh / screenCfg.rows), fw, r * (fh / screenCfg.rows));
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────────────────────────
function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  screenCfg.fullW = width  * screenCfg.cols;
  screenCfg.fullH = height * screenCfg.rows;
  initArchiveNodes();
}
