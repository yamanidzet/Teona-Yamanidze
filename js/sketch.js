// MISATTRIBUTION MACHINE — Thread & Particle System
// Visual reference: Memo Akten (Networked Condition), Mario Klingemann
//
// Each artwork is rendered as a cloud of luminous particles connected by threads.
// Misattribution = particles pulled into noise chaos, threads tangle wrongly.
// Truth = particles find their correct positions, threads form the real image.
//
// Phases:
//   PRISTINE      — Particles coalesce from void into the artwork form
//   LABEL_APPLY   — A thin archival mark settles over the image
//   CORRUPT       — Noise field tears particles from their correct positions
//   PROPAGATE     — Torn particles stream across screens to archive nodes
//   MACHINE_GAZE  — Cold scanner sweeps; particles freeze in wrong positions
//   INTERVENTION  — Warm force field draws particles back toward truth
//   TRUTH         — Particles lock into form; threads illuminate the artwork
//   FADE          — Particles dissolve back to void

let state, artworkImages = {}, currentArtist;
let phaseIndex = 0;
let particles  = [];
let archiveNodes = [];
let noiseOffset  = 0;
let screenCfg;
let imageManifest = [];

const N = 1800; // particle count

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

  spawnParticles(screenCfg.fullW, screenCfg.fullH, false);
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
    if (url && url.startsWith('http') && !artistFirst[a]) artistFirst[a] = url;
  }
  Object.entries(artistFirst).forEach(([artist, url]) => {
    loadImage(url, img => {
      img.loadPixels();
      artworkImages[artist] = img;
      if (artist === state.artist) seedParticlesFromImage(img);
    }, () => {});
  });
}

function buildState(artistName) {
  return {
    artist:     artistName,
    identity:   ARTWORK_IDENTITIES[artistName],
    phase:      PHASES.PRISTINE,
    phaseStart: millis(),
  };
}

// ── Particle spawn — scattered in void ───────────────────────────────────────
function spawnParticles(fw, fh, fromImage) {
  if (!fromImage) {
    particles = [];
    for (let i = 0; i < N; i++) {
      particles.push({
        x: random(fw), y: random(fh),
        vx: 0, vy: 0,
        tx: random(fw), ty: random(fh),
        brightness: random(70, 95),
        hueShift: random(-8, 8),
        size: random(1, 2.2),
      });
    }
  } else {
    // Scatter current particles to random void positions
    particles.forEach(p => {
      p.x = random(fw); p.y = random(fh);
      p.vx = random(-1, 1); p.vy = random(-1, 1);
    });
  }
}

// Seed particle targets from artwork image pixels (bias toward bright pixels)
function seedParticlesFromImage(img) {
  const fw   = screenCfg.fullW;
  const fh   = screenCfg.fullH;
  const cx   = fw / 2;
  const cy   = fh / 2;
  const diam = min(fw, fh) * 0.50;

  for (let i = 0; i < particles.length; i++) {
    let px, py, r, g, b;
    let tries = 0;
    do {
      px = int(random(img.width));
      py = int(random(img.height));
      const idx = (py * img.width + px) * 4;
      r = img.pixels[idx];
      g = img.pixels[idx + 1];
      b = img.pixels[idx + 2];
      tries++;
    } while ((r + g + b) / 3 < 25 && tries < 28);

    const bri = (r + g + b) / 3 / 255;
    particles[i].tx = cx + ((px / img.width)  - 0.5) * diam;
    particles[i].ty = cy + ((py / img.height) - 0.5) * diam;
    particles[i].brightness = 72 + bri * 24;
    particles[i].hueShift   = bri * 12 - 2;
  }
}

// Seed targets from artist glyph positions when no image available
function seedParticlesFromGlyph(fw, fh) {
  const cx = fw / 2, cy = fh / 2;
  const r  = min(fw, fh) * 0.24;
  for (let i = 0; i < particles.length; i++) {
    const a = state.artist;
    let tx, ty;
    if (a === 'Malevich') {
      // Grid of squares
      tx = cx + (random() - 0.5) * r * 2.2;
      ty = cy + (random() - 0.5) * r * 2.2;
    } else if (a === 'Exter') {
      // Hexagonal facets
      const ang = random(TWO_PI);
      const d   = sqrt(random()) * r;
      tx = cx + cos(ang) * d;
      ty = cy + sin(ang) * d;
    } else {
      // Radial ring
      const ang = random(TWO_PI);
      const d   = r * random(0.4, 1.0);
      tx = cx + cos(ang) * d;
      ty = cy + sin(ang) * d;
    }
    particles[i].tx = tx;
    particles[i].ty = ty;
    particles[i].brightness = random(72, 92);
  }
}

// ── Archive nodes ─────────────────────────────────────────────────────────────
function initArchiveNodes() {
  archiveNodes = ARCHIVE_CHAIN.map((arc, i) => ({
    ...arc,
    x: map(i, 0, ARCHIVE_CHAIN.length - 1, 0.1, 0.9),
    y: map(arc.tier, 0, 3, 0.15, 0.82),
    activated:   false,
    activatedAt: 0,
    pulse:       random(TWO_PI),
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
    initArchiveNodes();

    const img = artworkImages[currentArtist];
    if (img) seedParticlesFromImage(img);
    else     seedParticlesFromGlyph(screenCfg.fullW, screenCfg.fullH);

    spawnParticles(screenCfg.fullW, screenCfg.fullH, true);
  }

  if (next.id === PHASES.PROPAGATE.id) {
    archiveNodes.forEach((n, i) => {
      n.activated   = false;
      n.activatedAt = state.phaseStart + i * 700;
    });
  }
}

// ── Main draw ─────────────────────────────────────────────────────────────────
function draw() {
  const now     = millis();
  const elapsed = now - state.phaseStart;
  const t       = constrain(elapsed / state.phase.duration, 0, 1);

  if (elapsed > state.phase.duration) advancePhase();

  // Motion trail — semi-transparent black fades previous frame
  noStroke();
  fill(0, 0, 0, 14);
  rect(0, 0, width, height);

  push();
  translate(-screenCfg.col * width, -screenCfg.row * height);
  drawFullCanvas(t, now);
  pop();
}

// ── Full canvas ───────────────────────────────────────────────────────────────
function drawFullCanvas(t, now) {
  const fw  = screenCfg.fullW;
  const fh  = screenCfg.fullH;
  const cx  = fw / 2;
  const cy  = fh / 2;
  const pid = state.phase.id;

  noiseOffset += 0.0012;

  // Ensure particles are seeded on first PRISTINE if image just loaded
  if (pid === PHASES.PRISTINE.id && particles[0] && particles[0].tx === undefined) {
    const img = artworkImages[state.artist];
    if (img) seedParticlesFromImage(img);
    else     seedParticlesFromGlyph(fw, fh);
  }

  const corruption = phaseCorruption(pid, t);
  updateParticles(fw, fh, corruption, now);
  drawThreads(corruption);
  drawDots(corruption);

  // Overlays
  if (pid === PHASES.LABEL_APPLY.id)  labelOverlay (cx, cy, fw, fh, t);
  if (pid === PHASES.PROPAGATE.id)    propagateOverlay(cx, cy, fw, fh, t, now);
  if (pid === PHASES.MACHINE_GAZE.id) scannerOverlay  (cx, cy, fw, fh, t, now);
  if (pid === PHASES.INTERVENTION.id) interventionOverlay(cx, cy, fw, fh, t);
  if (pid === PHASES.FADE.id) {
    noStroke();
    fill(0, 0, 0, map(t, 0, 1, 0, 100));
    rect(0, 0, fw, fh);
  }

  drawScreenGrid(fw, fh);
}

// ── Corruption value — drives all particle behaviour ─────────────────────────
function phaseCorruption(pid, t) {
  if (pid === PHASES.PRISTINE.id)     return map(t, 0, 1, 1.0, 0.0);
  if (pid === PHASES.LABEL_APPLY.id)  return 0.04;
  if (pid === PHASES.CORRUPT.id)      return easeInOut(t);
  if (pid === PHASES.PROPAGATE.id)    return 0.88;
  if (pid === PHASES.MACHINE_GAZE.id) return 0.92;
  if (pid === PHASES.INTERVENTION.id) return map(t, 0, 1, 0.92, 0.04);
  if (pid === PHASES.TRUTH.id)        return map(t, 0, 1, 0.04, 0.0);
  if (pid === PHASES.FADE.id)         return 0.0;
  return 0;
}

// ── Particle physics ──────────────────────────────────────────────────────────
function updateParticles(fw, fh, corruption, now) {
  const spring   = lerp(0.055, 0.004, corruption); // strong spring when clean
  const damping  = 0.86;
  const noiseAmp = lerp(0.0, 4.2, corruption);
  const noiseScl = 180;

  for (let i = 0; i < particles.length; i++) {
    const p  = particles[i];

    // Spring toward target
    p.vx += (p.tx - p.x) * spring;
    p.vy += (p.ty - p.y) * spring;

    // Noise turbulence (misattribution force)
    if (noiseAmp > 0.05) {
      const n1 = noise(p.x / noiseScl,        p.y / noiseScl,        noiseOffset);
      const n2 = noise(p.x / noiseScl + 50.0, p.y / noiseScl + 30.0, noiseOffset);
      p.vx += cos(n1 * TWO_PI * 3) * noiseAmp;
      p.vy += sin(n2 * TWO_PI * 3) * noiseAmp;
    }

    p.vx *= damping;
    p.vy *= damping;
    p.x  += p.vx;
    p.y  += p.vy;

    // Soft boundary
    if (p.x < 0)   { p.x = 0;   p.vx *= -0.4; }
    if (p.x > fw)  { p.x = fw;  p.vx *= -0.4; }
    if (p.y < 0)   { p.y = 0;   p.vy *= -0.4; }
    if (p.y > fh)  { p.y = fh;  p.vy *= -0.4; }
  }
}

// ── Thread connections between nearby particles ───────────────────────────────
function drawThreads(corruption) {
  // Color: warm cream (clean) → cold dim blue (corrupt)
  const hue  = lerp(42,  195, corruption);
  const sat  = lerp(15,  30,  corruption);
  const bri  = lerp(92,  65,  corruption);
  const aBase = lerp(18,  8,  corruption);
  const maxD  = lerp(52,  110, corruption); // corruption = wider, looser mesh
  const maxD2 = maxD * maxD;

  strokeWeight(0.45);
  noFill();

  // Sample every 3rd particle as source; check next 90 for proximity
  for (let i = 0; i < particles.length; i += 3) {
    const a = particles[i];
    let drawn = 0;
    for (let j = i + 1; j < i + 90 && j < particles.length && drawn < 5; j++) {
      const b  = particles[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const d2 = dx * dx + dy * dy;
      if (d2 < maxD2) {
        const d = sqrt(d2);
        stroke(hue, sat, bri, map(d, 0, maxD, aBase, 0));
        line(a.x, a.y, b.x, b.y);
        drawn++;
      }
    }
  }
}

// ── Particle dots ─────────────────────────────────────────────────────────────
function drawDots(corruption) {
  const hue  = lerp(42, 200, corruption);
  const sat  = lerp(14, 28,  corruption);
  noStroke();

  for (let i = 0; i < particles.length; i++) {
    const p     = particles[i];
    const speed = sqrt(p.vx * p.vx + p.vy * p.vy);
    const alpha = lerp(80, 50, corruption) * constrain(map(speed, 0, 3, 1, 0.4), 0.4, 1);
    fill(hue + p.hueShift, sat, p.brightness, alpha);
    ellipse(p.x, p.y, p.size, p.size);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// OVERLAYS
// ─────────────────────────────────────────────────────────────────────────────

// LABEL_APPLY — thin white archival rectangle descending
function labelOverlay(cx, cy, fw, fh, t) {
  const enter = easeInOut(t);
  const mW    = fw * 0.38;
  const mH    = fh * 0.13;
  const mY    = lerp(-fh * 0.2, cy - min(fw, fh) * 0.17, enter);

  push();
  translate(cx, mY);
  rectMode(CENTER);
  noFill();
  stroke(0, 0, 88, 35 * enter);
  strokeWeight(0.8);
  rect(0, 0, mW, mH);

  // Horizontal rule lines — archival label structure
  stroke(0, 0, 75, 20 * enter);
  strokeWeight(0.5);
  for (let i = 0; i < 4; i++) {
    const ly = lerp(-mH * 0.3, mH * 0.3, i / 3);
    const lw = mW * (i === 1 ? 0.58 : 0.32);
    line(-lw / 2, ly, lw / 2, ly);
  }
  pop();
}

// PROPAGATE — archive network with animated thread signals
function propagateOverlay(cx, cy, fw, fh, t, now) {
  archiveNodes.forEach(node => {
    if (!node.activated && now >= node.activatedAt) node.activated = true;
    if (node.activated) node.pulse = (node.pulse + 0.028) % TWO_PI;
  });

  for (let i = 0; i < archiveNodes.length - 1; i++) {
    const a = archiveNodes[i];
    const b = archiveNodes[i + 1];
    if (!a.activated || !b.activated) continue;
    const ax = a.x * fw, ay = a.y * fh;
    const bx = b.x * fw, by = b.y * fh;

    noFill();
    stroke(0, 0, 58, 22);
    strokeWeight(0.7);
    beginShape();
    for (let s = 0; s <= 12; s++) {
      const r  = s / 12;
      const ix = lerp(ax, bx, r);
      const iy = lerp(ay, by, r);
      const n  = noise(ix / 260, iy / 260, noiseOffset) - 0.5;
      curveVertex(ix + n * 18, iy + n * 12);
    }
    endShape();

    // Signal dot travelling the thread
    const ft = (now % 2200) / 2200;
    fill(42, 18, 90, 75);
    noStroke();
    ellipse(lerp(ax, bx, ft), lerp(ay, by, ft), 5.5, 5.5);
  }

  archiveNodes.forEach(node => {
    if (!node.activated) return;
    const nx = node.x * fw, ny = node.y * fh;
    const ps = sin(node.pulse) * 4;
    noFill();
    stroke(0, 0, 55, 25);
    strokeWeight(0.7);
    ellipse(nx, ny, 30 + ps, 30 + ps);
    fill(42, 15, 88, 65);
    noStroke();
    ellipse(nx, ny, 6.5 + ps * 0.25, 6.5 + ps * 0.25);
  });
}

// MACHINE_GAZE — cold scanning light; clinical brackets
function scannerOverlay(cx, cy, fw, fh, t, now) {
  const scanY = (now / 750 * fh) % fh;
  const barH  = fh * 0.045;
  noStroke();
  for (let dy = 0; dy < barH; dy++) {
    fill(198, 22, 85, map(dy, 0, barH, 16 * t, 0));
    rect(0, (scanY + dy) % fh, fw, 1);
  }
  stroke(200, 18, 82, 32 * t);
  strokeWeight(0.9);
  line(0, scanY % fh, fw, scanY % fh);

  if (t > 0.35) {
    const rl  = min(fw, fh) * 0.20 * easeInOut(map(t, 0.35, 1, 0, 1));
    const gap = rl * 0.30;
    noFill();
    stroke(200, 18, 82, 28 * t);
    strokeWeight(0.9);
    for (let q = 0; q < 4; q++) {
      const qx = (q < 2 ? -1 : 1) * rl + cx;
      const qy = (q % 2 === 0 ? -1 : 1) * rl + cy;
      const ex = (q < 2 ? -1 : 1) * gap + cx;
      const ey = (q % 2 === 0 ? -1 : 1) * gap + cy;
      line(qx, qy, qx, ey);
      line(qx, qy, ex, qy);
    }
  }

  // Flicker at peak
  if (t > 0.82) {
    noStroke();
    fill(0, 0, 0, 25 * sin(now / 50) * easeInOut(map(t, 0.82, 1, 0, 1)));
    rect(0, 0, fw, fh);
  }
}

// INTERVENTION — warm light sweeping from the left
function interventionOverlay(cx, cy, fw, fh, t) {
  const reach = easeInOut(t) * fw;
  noStroke();
  for (let x = 0; x < reach; x += 2) {
    fill(42, 18, 100, map(x, 0, reach, 10, 0));
    rect(x, 0, 2, fh);
  }
  stroke(42, 20, 96, 36 * easeInOut(t));
  strokeWeight(1.2);
  line(reach, 0, reach, fh);
}

// ── Screen grid ───────────────────────────────────────────────────────────────
function drawScreenGrid(fw, fh) {
  stroke(0, 0, 100, 5);
  strokeWeight(1);
  for (let c = 1; c < screenCfg.cols; c++)
    line(c * (fw / screenCfg.cols), 0, c * (fw / screenCfg.cols), fh);
  for (let r = 1; r < screenCfg.rows; r++)
    line(0, r * (fh / screenCfg.rows), fw, r * (fh / screenCfg.rows));
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  screenCfg.fullW = width  * screenCfg.cols;
  screenCfg.fullH = height * screenCfg.rows;
  initArchiveNodes();
}
