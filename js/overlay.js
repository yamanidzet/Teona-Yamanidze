// Step-by-step phase overlay — no kiosk interaction
// Receives 'phaseChange' events from sketch.js and updates the UI

const PHASE_STEPS = {
  pristine: {
    step: '01 / 08',
    title: 'Pristine',
    desc: 'The artwork appears whole — 1,800 particles coalescing from void into its original form, before any archive touched it.',
  },
  label_apply: {
    step: '02 / 08',
    title: 'Label Applied',
    desc: 'An archival stamp descends. The wrong national identity is recorded. One catalogue entry, one wrong word — the error begins here.',
  },
  corrupt: {
    step: '03 / 08',
    title: 'Corruption',
    desc: 'A noise field tears the particles from their correct positions. The image fractures as misattribution distorts the record.',
  },
  propagate: {
    step: '04 / 08',
    title: 'Propagation',
    desc: 'The error flows downstream: Library of Congress → WorldCat → Trove → Museum catalogues → AI systems. Six nodes, one chain.',
  },
  machine_gaze: {
    step: '05 / 08',
    title: 'Machine Gaze',
    desc: 'Three AI systems (Claude, GPT-4o, LLAMA) scan the corrupted record. A cold scanner sweeps. All three confirm the wrong identity.',
  },
  intervention: {
    step: '06 / 08',
    title: 'Intervention',
    desc: 'A warm beam of light cuts through. The researcher\'s correction. Correct-identity data reclaims the particles from noise.',
  },
  truth: {
    step: '07 / 08',
    title: 'Truth Restored',
    desc: 'Particles lock to their correct positions. The artwork is whole again — and correctly attributed to its actual cultural origin.',
  },
  fade: {
    step: '08 / 08',
    title: 'Fade',
    desc: 'The cycle resets. The next artist begins. The loop continues — as the error does in the archive, until each record is corrected.',
  },
};

const ARTIST_DESCRIPTIONS = {
  Malevich: {
    flawed:   'Russian / Soviet',
    correct:  'Ukrainian-born (Kyiv, 1879); Polish ethnic heritage',
    detail:   'Born in Kyiv, capital of Ukraine. The label "Russian artist" conflates Soviet statehood with his Ukrainian origin.',
    records:  '272 records examined — 195 contain wrong-label misattribution',
  },
  Exter: {
    flawed:   'Russian avant-garde',
    correct:  'Ukrainian-born (Kyiv); trained Kyiv School of Art',
    detail:   'Born in Białystok, raised and trained in Kyiv. Consistently misframed as "Russian" — often structurally, through exhibition titles.',
    records:  '44 records examined — 38 contain wrong-label misattribution',
  },
  Kakabadze: {
    flawed:   'Société Anonyme "Russian avant-garde" canon',
    correct:  'Georgian-born (Kutaisi/Tbilisi); Paris 1919–1927',
    detail:   'Born in Kutaisi, Georgia. Absorbed into the "Russian avant-garde" via the 1984 Herbert Catalogue Raisonné — structural misattribution invisible at field level.',
    records:  '19 records examined — 19 contain structural misattribution',
  },
  Pagava: {
    flawed:   'Empire Russe (birthplace erasure)',
    correct:  'Georgian-born (Tbilisi); émigré to Paris 1923',
    detail:   'Born in Tbilisi, Georgia. The Pompidou label "Empire Russe" perpetuates imperial erasure of Georgian nationhood.',
    records:  '19 records examined — all 19 use imperial framing',
  },
  Parajanov: {
    flawed:   'Soviet (erasing ethnicity and birthplace)',
    correct:  'Soviet-Armenian; born Sarkis Parajanov in Tbilisi, Georgia',
    detail:   '304 of 305 bibliographic records label him simply "Soviet" — erasing his Armenian ethnic identity and Georgian birthplace.',
    records:  '305 bibliographic records — 304 omit Armenian identity',
  },
};

function initOverlay() {
  window.addEventListener('phaseChange', e => {
    const { phaseLabel, artist, identity } = e.detail;
    updatePhasePanel(phaseLabel);
    updateArtistPanel(artist);
  });
}

function updatePhasePanel(label) {
  const info = PHASE_STEPS[label] || PHASE_STEPS.pristine;
  const el = document.getElementById('phase-overlay');
  if (!el) return;
  el.querySelector('.step-num').textContent  = info.step;
  el.querySelector('.step-title').textContent = info.title;
  el.querySelector('.step-desc').textContent  = info.desc;
  el.classList.add('flash');
  setTimeout(() => el.classList.remove('flash'), 600);
}

function updateArtistPanel(artist) {
  const info = ARTIST_DESCRIPTIONS[artist] || {};
  const el = document.getElementById('artist-overlay');
  if (!el) return;
  el.querySelector('.artist-name').textContent    = artist;
  el.querySelector('.artist-flawed').textContent  = '✗ ' + (info.flawed  || '');
  el.querySelector('.artist-correct').textContent = '✓ ' + (info.correct || '');
  el.querySelector('.artist-detail').textContent  = info.detail  || '';
  el.querySelector('.artist-records').textContent = info.records || '';
}

document.addEventListener('DOMContentLoaded', initOverlay);
