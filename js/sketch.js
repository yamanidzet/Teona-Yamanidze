// MISATTRIBUTION MACHINE — The Book of Forms
// Organic botanical aesthetic: warm amber, sepia, deep green
// Film grain overlay throughout
//
// Phases:
//   PRISTINE      — Artwork as botanical plate on warm parchment
//   LABEL_APPLY   — An archival stamp descends like a pressed seal
//   CORRUPT       — Tendrils of misattribution colonise the image
//   PROPAGATE     — Mycelium spreads through archive network; spores release
//   MACHINE_GAZE  — Cold UV scanner drains warmth; organic forms crystallise
//   INTERVENTION  — Amber light floods back from the edge
//   TRUTH         — Overgrowth falls away as petals; artwork blooms whole
//   FADE          — Cycle resets to next artist

let state, artworkImages = {}, currentArtist;
let phaseIndex = 0;
let particles = [], archiveNodes = [], tendrils = [];
let noiseOffset = 0;
let screenCfg;
let imageManifest = [];

// ── Colour palette — warm and botanical ──────────────────────────────────────
// All values are [hue, sat, bri] for colorMode(HSB, 360, 100, 100, 100)
const PAL = {
  bg:          [25,  30,  5 ],   // deep warm black
  parchment:   [38,  18,  91],   // warm paper ground
  amber:       [35,  78,  86],   // warm amber
  amberDeep:   [28,  65,  52],   // deep amber / sepia
  sepia:       [22,  52,  45],   // dark sepia
  tendril:     [152, 28,  42],   // cold grey-green (misattribution)
  tendrilDark: [145, 35,  24],   // darker tendril
  scanner:     [192, 20,  82],   // cold scanner
  petal:       [40,  45,  88],   // falling petal
  vein:        [35,  55,  72],   // amber vein
  spore:       [38,  60,  78],   // warm spore
};

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
  generateTendrils();

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

// ── Particles — warm spore-dust ───────────────────────────────────────────────
function initParticles() {
  particles = [];
  const fw = screenCfg.fullW || width;
  const fh = screenCfg.fullH || height;
  for (let i = 0; i < 200; i++) {
    particles.push({
      x:       random(fw),
      y:       random(fh),
      vx:      random(-0.15, 0.15),
      vy:      random(-0.32, -0.04),
      size:    random(1, 3.5),
      life:    random(200),
      maxLife: random(160, 340),
      hOff:    random(20),
    });
  }
}

// ── Tendrils — pre-generated organic misattribution paths ─────────────────────
function generateTendrils() {
  const fw = screenCfg.fullW || width;
  const fh = screenCfg.fullH || height;
  tendrils = [];
  const cx = fw / 2;
  const cy = fh / 2;
  const count = 32;

  for (let i = 0; i < count; i++) {
    // Each tendril starts near image boundary and grows outward
    const angle  = TWO_PI * i / count + random(-0.2, 0.2);
    const startR = min(fw, fh) * random(0.2, 0.3);
    let px = cx + cos(angle) * startR;
    let py = cy + sin(angle) * startR;
    const seed  = random(1000);
    const steps = int(random(30, 65));
    const pts   = [];

    for (let s = 0; s < steps; s++) {
      pts.push({ x: px, y: py });
      const n    = noise(px / 280, py / 280, seed + s * 0.03);
      const dir  = angle + (n - 0.5) * 2.2;
      const spd  = random(10, 22);
      px += cos(dir) * spd;
      py += sin(dir) * spd;
      px = constrain(px, -fw * 0.15, fw * 1.15);
      py = constrain(py, -fh * 0.15, fh * 1.15);
    }

    tendrils.push({
      points:    pts,
      delay:     random(0, 0.52),
      thickness: random(0.5, 2.8),
      hue:       random(138, 162),
      sat:       random(18, 35),
      bri:       random(26, 50),
    });
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
    initParticles();
    initArchiveNodes();
    generateTendrils();
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

  const ox = -screenCfg.col * width;
  const oy = -screenCfg.row * height;

  background(...PAL.bg);

  push();
  translate(ox, oy);
  drawFullCanvas(t, now);
  pop();
}

function drawFullCanvas(t, now) {
  const fw  = screenCfg.fullW;
  const fh  = screenCfg.fullH;
  const cx  = fw / 2;
  const cy  = fh / 2;
  const pid = state.phase.id;

  noiseOffset += 0.0018;

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
    fill(...PAL.bg, map(t, 0, 1, 0, 100));
    rect(0, 0, fw, fh);
  }

  drawFilmGrain(fw, fh, now);
  drawScreenGrid(fw, fh);
}

// ── Film grain — warm sepia noise layer, constant ────────────────────────────
function drawFilmGrain(fw, fh, now) {
  randomSeed(int(now / 42));
  noStroke();
  for (let i = 0; i < 1100; i++) {
    const gx = random(fw);
    const gy = random(fh);
    const gs = random(0.4, 2.0);
    const ga = random(3, 16);
    fill(28, random(18, 42), random(55, 82), ga);
    ellipse(gx, gy, gs, gs);
  }
  randomSeed();
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. PRISTINE — botanical plate: warm parchment, amber leaf-vein filaments
// ─────────────────────────────────────────────────────────────────────────────
function drawPristine(cx, cy, fw, fh, t, now) {
  const img   = artworkImages[state.artist];
  const size  = min(fw, fh) * 0.50 * easeInOut(t);
  const enter = easeInOut(t);

  push();
  translate(cx, cy);
  noStroke();

  // Warm parchment oval behind image
  for (let r = size * 0.98; r > 0; r -= 14) {
    fill(...PAL.parchment, map(r, 0, size * 0.98, 30, 0) * enter);
    ellipse(0, 0, r * 2.15, r * 1.85);
  }

  // Amber vein filaments radiating like pressed leaf
  drawVeins(size, enter, now);

  if (img) {
    tint(...PAL.amber, 88 * enter);
    imageMode(CENTER);
    image(img, 0, 0, size, size);
    noTint();
  } else {
    drawGlyph(size * 0.5, enter, 0);
  }
  pop();

  drawSpores(0.20 * enter, fw, fh, 'warm');
}

// Draw amber vein filaments radiating from centre
function drawVeins(size, alpha, now) {
  const count = 18;
  noFill();
  for (let i = 0; i < count; i++) {
    const baseAngle = TWO_PI * i / count;
    const len       = size * (0.55 + noise(i * 0.4, noiseOffset * 0.5) * 0.55);
    strokeWeight(0.6 + noise(i * 0.2) * 0.8);
    stroke(...PAL.vein, 20 * alpha);
    beginShape();
    for (let s = 0; s <= 14; s++) {
      const ratio = s / 14;
      const ang   = baseAngle + (noise(i * 0.5, ratio * 1.8, noiseOffset * 0.3) - 0.5) * 0.7;
      const d     = len * ratio;
      curveVertex(cos(ang) * d, sin(ang) * d);
    }
    endShape();
    // Branch tips
    if (alpha > 0.55) {
      const tipX = cos(baseAngle) * len * 0.92;
      const tipY = sin(baseAngle) * len * 0.92;
      stroke(...PAL.vein, 13 * alpha);
      strokeWeight(0.35);
      for (let b = 0; b < 3; b++) {
        const bAng = baseAngle + random(-0.55, 0.55);
        const bLen = len * random(0.06, 0.16);
        line(tipX, tipY, tipX + cos(bAng) * bLen, tipY + sin(bAng) * bLen);
      }
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. LABEL APPLY — archival stamp descends like a pressed wax seal
// ─────────────────────────────────────────────────────────────────────────────
function drawLabelApply(cx, cy, fw, fh, t, now) {
  drawPristine(cx, cy, fw, fh, 1, now);

  const enter = easeInOut(t);
  const markW = fw * 0.40;
  const markH = fh * 0.16;
  const markY = lerp(-fh * 0.22, cy - min(fw, fh) * 0.14, enter);
  const markA = 82 * enter;

  push();
  translate(cx, markY);
  rectMode(CENTER);

  // Outer border — sepia, like aged authority
  noFill();
  stroke(...PAL.amberDeep, markA * 0.55);
  strokeWeight(2.5);
  rect(0, 0, markW, markH, 5);

  // Inner fill — deep sepia ground
  fill(...PAL.sepia, markA * 0.82);
  noStroke();
  rect(0, 0, markW - 6, markH - 6, 3);

  // Abstract bar lines — archival authority structure, no text
  const barCount = 5;
  for (let i = 0; i < barCount; i++) {
    const barY = lerp(-markH * 0.3, markH * 0.3, i / (barCount - 1));
    const barW = markW * (i === 2 ? 0.60 : 0.32 + noise(i * 0.7) * 0.15);
    fill(...PAL.amber, 32 * enter);
    noStroke();
    rect(0, barY, barW, markH * 0.055, 1);
  }

  // Impact rings when stamp lands — organic ripple
  if (t > 0.70) {
    const impact = easeInOut(map(t, 0.70, 1, 0, 1));
    for (let r = 1; r <= 5; r++) {
      const rr = r * 85 * impact;
      noFill();
      stroke(...PAL.amber, max(0, 28 - r * 5) * impact);
      strokeWeight(0.8);
      ellipse(0, cy - markY, rr * 2, rr * 1.35);
    }
  }
  pop();
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. CORRUPT — organic tendrils colonise the image; warmth retreats
// ─────────────────────────────────────────────────────────────────────────────
function drawCorrupt(cx, cy, fw, fh, t, now) {
  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.50;

  // Fading parchment ground — warmth retreating
  push();
  translate(cx, cy);
  noStroke();
  for (let r = size * 0.92; r > 0; r -= 16) {
    fill(...PAL.parchment, map(r, 0, size * 0.92, 20, 0) * (1 - t * 0.65));
    ellipse(0, 0, r * 2.15, r * 1.85);
  }

  // Image dimming under overgrowth
  if (img) {
    const warmLoss = t * 50;
    tint(28, max(0, 78 - warmLoss), max(0, 86 - warmLoss * 0.6), 88 - t * 58);
    imageMode(CENTER);
    image(img, 0, 0, size, size);
    noTint();
  } else {
    drawGlyph(size * 0.5, 1 - t * 0.55, t * 0.45);
  }
  pop();

  // Growing tendrils colonising the image
  drawTendrils(t, fw, fh, 1.0);

  // Cold surface haze
  if (t > 0.38) {
    const cta = easeInOut(map(t, 0.38, 1, 0, 1));
    noStroke();
    for (let y = 0; y < fh; y += 10) {
      const n = noise(y / 380, noiseOffset * 0.4);
      fill(...PAL.tendril, n * 9 * cta);
      rect(0, y, fw, 2);
    }
  }
}

// Render growing tendrils up to proportion t
function drawTendrils(t, fw, fh, alpha) {
  strokeCap(ROUND);
  noFill();
  tendrils.forEach(td => {
    if (t < td.delay) return;
    const tdT  = constrain(map(t, td.delay, 1, 0, 1), 0, 1);
    const drawn = int(td.points.length * tdT);
    if (drawn < 2) return;

    stroke(td.hue, td.sat, td.bri, 68 * alpha * easeInOut(tdT));
    strokeWeight(td.thickness);
    beginShape();
    for (let i = 0; i < drawn; i++) {
      curveVertex(td.points[i].x, td.points[i].y);
    }
    endShape();

    // Tiny fork at growing tip
    if (drawn > 3 && tdT > 0.2) {
      const tip  = td.points[drawn - 1];
      const prev = td.points[Math.max(0, drawn - 3)];
      const dir  = atan2(tip.y - prev.y, tip.x - prev.x);
      stroke(td.hue, td.sat, td.bri, 38 * alpha * easeInOut(tdT));
      strokeWeight(td.thickness * 0.42);
      for (let b = 0; b < 2; b++) {
        const bAng = dir + (b === 0 ? 0.52 : -0.52);
        const bLen = random(10, 28);
        line(tip.x, tip.y, tip.x + cos(bAng) * bLen, tip.y + sin(bAng) * bLen);
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. PROPAGATE — mycelium threads through archive network; spores drift
// ─────────────────────────────────────────────────────────────────────────────
function drawPropagate(cx, cy, fw, fh, t, now) {
  drawCorrupt(cx, cy, fw, fh, 0.85, now);

  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.12;

  // Activate archive nodes sequentially
  archiveNodes.forEach(node => {
    if (!node.activated && now >= node.activatedAt) node.activated = true;
    if (node.activated) node.pulse = (node.pulse + 0.033) % TWO_PI;
  });

  // Mycelium connections — noisy curved threads between nodes
  for (let i = 0; i < archiveNodes.length - 1; i++) {
    const a = archiveNodes[i];
    const b = archiveNodes[i + 1];
    if (!a.activated || !b.activated) continue;
    const ax = a.x * fw, ay = a.y * fh;
    const bx = b.x * fw, by = b.y * fh;

    noFill();
    stroke(...PAL.tendril, 38);
    strokeWeight(0.85);
    beginShape();
    const segs = 14;
    for (let s = 0; s <= segs; s++) {
      const ratio = s / segs;
      const ix = lerp(ax, bx, ratio);
      const iy = lerp(ay, by, ratio);
      const n  = noise(ix / 220, iy / 220, noiseOffset * 0.4);
      curveVertex(ix + (n - 0.5) * 44, iy + (n - 0.5) * 30);
    }
    endShape();

    // Travelling spore — warm amber dot moving along thread
    const ft = (now % 2400) / 2400;
    fill(...PAL.spore, 72);
    noStroke();
    ellipse(lerp(ax, bx, ft), lerp(ay, by, ft), 7, 7);
  }

  // Archive nodes — styled as pressed botanical specimens
  archiveNodes.forEach(node => {
    if (!node.activated) return;
    const nx = node.x * fw;
    const ny = node.y * fh;
    const ps = sin(node.pulse) * 5;
    noFill();
    stroke(...PAL.tendril, 38);
    strokeWeight(1);
    ellipse(nx, ny, 40 + ps, 40 + ps);
    stroke(...PAL.tendril, 22);
    strokeWeight(0.6);
    line(nx - 13, ny, nx + 13, ny);
    line(nx, ny - 13, nx, ny + 13);
    fill(...PAL.amberDeep, 68);
    noStroke();
    ellipse(nx, ny, 9 + ps * 0.3, 9 + ps * 0.3);
  });

  // Corrupted specimen copies at grid positions
  const positions = [
    [fw * 0.11, fh * 0.13], [fw * 0.89, fh * 0.13],
    [fw * 0.11, fh * 0.87], [fw * 0.89, fh * 0.87],
    [fw * 0.50, fh * 0.10], [fw * 0.50, fh * 0.90],
  ];
  positions.forEach(([bx, by], i) => {
    const threshold = i * 0.13;
    if (t < threshold) return;
    const copyT = constrain(map(t, threshold, threshold + 0.20, 0, 1), 0, 1);
    push();
    translate(bx, by);
    noStroke();
    fill(...PAL.parchment, 16 * copyT);
    ellipse(0, 0, size * 3.6, size * 2.9);
    // Tendril overgrowth on each copy
    noFill();
    stroke(...PAL.tendril, 48 * copyT);
    strokeWeight(0.65);
    for (let td = 0; td < 6; td++) {
      const ang = random(TWO_PI);
      const len = random(size * 0.4, size * 1.1);
      beginShape();
      for (let s = 0; s <= 7; s++) {
        const r  = (s / 7) * len;
        const a2 = ang + (noise(td * 0.5, s * 0.4, noiseOffset) - 0.5) * 1.5;
        curveVertex(cos(a2) * r, sin(a2) * r);
      }
      endShape();
    }
    if (img) {
      tint(...PAL.tendril, 42 * copyT);
      imageMode(CENTER);
      image(img, 0, 0, size * 2.3, size * 2.3);
      noTint();
    } else {
      drawGlyph(size * 0.8, copyT, 0.5);
    }
    pop();
  });

  drawSpores(0.38 * t, fw, fh, 'cold');
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. MACHINE_GAZE — cold UV scanner; warmth drains; organic forms crystallise
// ─────────────────────────────────────────────────────────────────────────────
function drawMachineGaze(cx, cy, fw, fh, t, now) {
  drawCorrupt(cx, cy, fw, fh, 0.80, now);

  // Cold colour overlay — progressively draining warmth
  noStroke();
  fill(192, 18, 14, 55 * easeInOut(t));
  rect(0, 0, fw, fh);

  const scanSystems = [
    { speed: 660,  offset: 0,         bri: 80, sat: 14 },
    { speed: 1100, offset: fh * 0.34, bri: 62, sat: 11 },
    { speed: 880,  offset: fh * 0.67, bri: 72, sat: 17 },
  ];

  scanSystems.forEach((sys, si) => {
    if (t < si * 0.20) return;
    const sysT  = constrain(map(t, si * 0.20, si * 0.20 + 0.38, 0, 1), 0, 1);
    const scanY = ((now / sys.speed * fh) + sys.offset) % fh;
    const barH  = lerp(1, fh * 0.05, sysT);

    noStroke();
    for (let dy = 0; dy < barH; dy++) {
      const a = map(dy, 0, barH, 20 * sysT, 0);
      fill(192, sys.sat, sys.bri, a);
      rect(0, (scanY + dy) % fh, fw, 1);
    }
    stroke(195, sys.sat, sys.bri, 38 * sysT);
    strokeWeight(1);
    line(0, scanY % fh, fw, scanY % fh);

    // Clinical corner targeting brackets
    if (sysT > 0.5) {
      const rl  = min(fw, fh) * 0.22 * easeInOut(map(sysT, 0.5, 1, 0, 1));
      const gap = rl * 0.28;
      noFill();
      stroke(195, sys.sat + 5, sys.bri, 33 * sysT);
      strokeWeight(1);
      for (let q = 0; q < 4; q++) {
        const qx = (q < 2 ? -1 : 1) * rl + cx;
        const qy = (q % 2 === 0 ? -1 : 1) * rl + cy;
        const ex = (q < 2 ? -1 : 1) * gap + cx;
        const ey = (q % 2 === 0 ? -1 : 1) * gap + cy;
        line(qx, qy, qx, ey);
        line(qx, qy, ex, qy);
      }
    }
  });

  // Final flicker — systems confirm the wrong label
  if (t > 0.84) {
    const flicker = sin(now / 55) * 0.5 + 0.5;
    noStroke();
    fill(0, 0, 0, 28 * flicker * easeInOut(map(t, 0.84, 1, 0, 1)));
    rect(0, 0, fw, fh);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. INTERVENTION — amber light sweeps back; tendrils wilt
// ─────────────────────────────────────────────────────────────────────────────
function drawIntervention(cx, cy, fw, fh, t, now) {
  // Corruption fades as amber returns
  drawCorrupt(cx, cy, fw, fh, 1 - t * 0.90, now);

  const sweep = easeInOut(t) * fw;

  // Amber wash sweeping from left
  noStroke();
  for (let x = 0; x < sweep; x += 1) {
    const a = map(x, 0, sweep, 30, 0) * easeInOut(t);
    fill(...PAL.amber, a);
    rect(x, 0, 1, fh);
  }
  // Leading warm edge
  stroke(...PAL.amber, 52 * easeInOut(t));
  strokeWeight(2.2);
  line(sweep, 0, sweep, fh);

  // Image re-emerging in warmth
  const img    = artworkImages[state.artist];
  const emerge = easeInOut(t);
  push();
  translate(cx, cy);
  noStroke();
  // Parchment ground returning
  for (let r = min(fw, fh) * 0.32 * emerge; r > 0; r -= 14) {
    fill(...PAL.parchment, map(r, 0, min(fw, fh) * 0.32, 24, 0) * emerge);
    ellipse(0, 0, r * 2.1, r * 1.85);
  }
  if (img) {
    tint(...PAL.amber, 80 * emerge);
    imageMode(CENTER);
    const sz = min(fw, fh) * 0.50 * emerge;
    image(img, 0, 0, sz, sz);
    noTint();
  } else {
    drawGlyph(min(fw, fh) * 0.26 * emerge, emerge, 0);
  }
  pop();

  // Tendrils wilting — fading as warmth returns
  drawTendrils(1, fw, fh, 1 - t * 0.92);
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. TRUTH — overgrowth falls as petals; artwork blooms in full amber warmth
// ─────────────────────────────────────────────────────────────────────────────
function drawTruth(cx, cy, fw, fh, t, now) {
  const img  = artworkImages[state.artist];
  const size = min(fw, fh) * 0.50;

  // Warm light wash across canvas
  noStroke();
  for (let y = 0; y < fh; y += 5) {
    const n = noise(y / 650, noiseOffset * 0.22);
    fill(...PAL.amber, n * 6 * t);
    rect(0, y, fw, 1);
  }

  // Central image — luminous, whole
  push();
  translate(cx, cy);
  noStroke();

  // Luminous parchment ground
  for (let r = size * 0.88; r > 0; r -= 12) {
    fill(...PAL.parchment, map(r, 0, size * 0.88, 34, 0) * t);
    ellipse(0, 0, r * 2.15, r * 1.85);
  }
  // Amber halo
  for (let r = size * 0.72; r > 0; r -= 20) {
    fill(...PAL.amber, map(r, 0, size * 0.72, 16, 0) * t);
    ellipse(0, 0, r * 2, r * 2);
  }

  if (img) {
    tint(...PAL.amber, 94 * t);
    imageMode(CENTER);
    image(img, 0, 0, size * easeInOut(t), size * easeInOut(t));
    noTint();
  } else {
    drawGlyph(size * 0.5 * easeInOut(t), 1, 0);
  }

  // Amber veins reclaimed — radiating clearly
  drawVeins(size * 1.22, t, now);
  pop();

  // Falling organic matter — tendrils releasing as petals
  drawFallingPetals(t, cx, cy, fw, fh, now);

  // Orbiting satellite images — correctly attributed, freely circulating
  const satCount = 5;
  for (let i = 0; i < satCount; i++) {
    const threshold = i * 0.14;
    if (t < threshold) continue;
    const satT  = constrain(map(t, threshold, threshold + 0.26, 0, 1), 0, 1);
    const angle = TWO_PI * i / satCount + now / 15000;
    const orb   = min(fw, fh) * 0.44;
    const bx    = cx + cos(angle) * orb;
    const by    = cy + sin(angle) * orb * 0.70;
    const sz    = size * 0.20 * easeInOut(satT);

    stroke(...PAL.vein, 14 * satT);
    strokeWeight(0.75);
    line(cx, cy, bx, by);

    push();
    translate(bx, by);
    noStroke();
    for (let r = sz * 0.92; r > 0; r -= 10) {
      fill(...PAL.parchment, map(r, 0, sz * 0.92, 22, 0) * satT);
      ellipse(0, 0, r * 2.1, r * 1.8);
    }
    if (img) {
      tint(...PAL.amber, 72 * satT);
      imageMode(CENTER);
      image(img, 0, 0, sz, sz);
      noTint();
    } else {
      drawGlyph(sz * 0.5, satT, 0);
    }
    pop();
  }

  drawSpores(0.48 * t, fw, fh, 'warm');
}

// ── Falling petals — former tendrils releasing as organic matter ──────────────
function drawFallingPetals(t, cx, cy, fw, fh, now) {
  if (t < 0.08) return;
  randomSeed(42);
  const petalCount = int(50 * t);
  for (let i = 0; i < petalCount; i++) {
    const delay  = random(0, 0.65);
    if (t < delay) {
      // Consume the random calls to keep positions consistent
      for (let skip = 0; skip < 7; skip++) random();
      continue;
    }
    const petalT = constrain(map(t, delay, 1, 0, 1), 0, 1);
    const px     = random(fw);
    const startY = cy + random(-min(fw, fh) * 0.32, min(fw, fh) * 0.18);
    const drift  = random(-fw * 0.06, fw * 0.06);
    const py     = startY + easeInOut(petalT) * fh * random(0.28, 0.70);
    const psize  = random(3, 14);
    const rot    = random(TWO_PI) + petalT * random(0.5, 2.5);
    const hue    = random(24, 46);
    const alpha  = max(0, 65 * (1 - petalT * 0.72));

    push();
    translate(px + drift * petalT, py);
    rotate(rot);
    fill(hue, random(28, 52), random(70, 90), alpha);
    noStroke();
    beginShape();
    curveVertex(0, -psize);
    curveVertex(psize * 0.52, 0);
    curveVertex(0, psize);
    curveVertex(-psize * 0.52, 0);
    curveVertex(0, -psize);
    endShape(CLOSE);
    pop();
  }
  randomSeed();
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared glyph — fallback when no artwork image is loaded
// Each artist has a distinct abstract form in warm amber palette
// ─────────────────────────────────────────────────────────────────────────────
function drawGlyph(r, alpha, corruptAmt) {
  const a = state.artist;

  if (corruptAmt > 0) {
    for (let i = 0; i < 9; i++) {
      const angle = TWO_PI * i / 9 + corruptAmt * random(-0.45, 0.45);
      const dist  = r * random(0.4, 1.0);
      fill(...PAL.tendril, 55 * alpha);
      noStroke();
      push();
      translate(cos(angle) * dist, sin(angle) * dist);
      rotate(random(TWO_PI));
      rect(-r * 0.11, -r * 0.04, r * 0.22, r * 0.08);
      pop();
    }
    return;
  }

  fill(...PAL.amber, 80 * alpha);
  noStroke();

  if (a === 'Malevich') {
    // Suprematist — geometric squares
    rectMode(CENTER);
    rect(0, 0, r * 0.90, r * 0.90);
    fill(...PAL.amberDeep, 75 * alpha);
    rect(r * 0.18, r * 0.18, r * 0.44, r * 0.18);
    fill(...PAL.parchment, 68 * alpha);
    rect(-r * 0.28, -r * 0.05, r * 0.16, r * 0.54);

  } else if (a === 'Exter') {
    // Cubo-Futurist — faceted planes
    for (let i = 0; i < 6; i++) {
      const ang  = TWO_PI * i / 6 + PI / 6;
      const ang2 = TWO_PI * ((i + 1) % 6) / 6 + PI / 6;
      fill(map(i, 0, 5, 25, 42), map(i, 0, 5, 48, 78), map(i, 0, 5, 44, 86), 70 * alpha);
      triangle(0, 0,
        cos(ang)  * r * 0.55, sin(ang)  * r * 0.55,
        cos(ang2) * r * 0.55, sin(ang2) * r * 0.55);
    }

  } else if (a === 'Pagava') {
    // Lyrical abstraction — organic flowing form
    beginShape();
    for (let ang = 0; ang < TWO_PI; ang += 0.17) {
      const nr = r * 0.52 * (1 + 0.24 * sin(ang * 3 + noiseOffset * 2));
      vertex(cos(ang) * nr, sin(ang) * nr);
    }
    endShape(CLOSE);
    fill(...PAL.amberDeep, 62 * alpha);
    ellipse(0, -r * 0.12, r * 0.22, r * 0.33);

  } else if (a === 'Kakabadze') {
    // Constructivist sail forms
    triangle(-r * 0.5, r * 0.44, 0, -r * 0.5, r * 0.44, r * 0.10);
    fill(...PAL.amberDeep, 60 * alpha);
    triangle(-r * 0.12, r * 0.5, r * 0.5, r * 0.12, r * 0.28, -r * 0.44);
    fill(...PAL.parchment, 54 * alpha);
    ellipse(-r * 0.14, -r * 0.14, r * 0.38, r * 0.38);

  } else if (a === 'Parajanov') {
    // Radial mosaic — film frame sections
    for (let i = 0; i < 12; i++) {
      const ang  = TWO_PI * i / 12;
      const ang2 = TWO_PI * (i + 1) / 12;
      const hue  = map(i % 3, 0, 2, 25, 42);
      const sat  = map(i % 3, 0, 2, 42, 76);
      const bri  = map(i % 3, 0, 2, 44, 84);
      fill(hue, sat, bri, 70 * alpha);
      arc(0, 0, r * 1.1, r * 1.1, ang, ang2, PIE);
    }
    fill(...PAL.bg, 82 * alpha);
    ellipse(0, 0, r * 0.20, r * 0.20);
  }

  noStroke();
  fill(...PAL.amber, 72 * alpha);
  ellipse(0, 0, r * 0.07, r * 0.07);
}

// ── Spore particles — warm or cold depending on phase ────────────────────────
function drawSpores(alpha, fw, fh, mode) {
  noStroke();
  particles.forEach(p => {
    p.x += p.vx;
    p.y += p.vy;
    p.life++;
    if (p.life > p.maxLife || p.y < 0 || p.x < 0 || p.x > fw) {
      p.x = random(fw); p.y = fh + p.size;
      p.vy = random(-0.33, -0.05); p.vx = random(-0.17, 0.17); p.life = 0;
    }
    const lr  = 1 - p.life / p.maxLife;
    const hue = mode === 'cold' ? 150 + p.hOff * 0.2 : 30 + p.hOff * 0.7;
    const sat = mode === 'cold' ? 24 : 52;
    const bri = mode === 'cold' ? 46 : 80;
    fill(hue, sat, bri, 48 * lr * alpha);
    ellipse(p.x, p.y, p.size * lr, p.size * lr);
  });
}

// ── Screen grid — faint amber lines marking panel boundaries ─────────────────
function drawScreenGrid(fw, fh) {
  stroke(...PAL.amberDeep, 10);
  strokeWeight(1);
  for (let c = 1; c < screenCfg.cols; c++) {
    line(c * (fw / screenCfg.cols), 0, c * (fw / screenCfg.cols), fh);
  }
  for (let r = 1; r < screenCfg.rows; r++) {
    line(0, r * (fh / screenCfg.rows), fw, r * (fh / screenCfg.rows));
  }
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
