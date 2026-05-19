// Dataset management — artworks and bibliographic records

// All artists share a neutral visual identity.
// Distortion = misattribution. Clarity = truth.
// No colour coding tied to national identity.

const ARTWORK_IDENTITIES = {
  Malevich: {
    name:        'Kazimir Malevich',
    true_label:  'Ukrainian-born (Kyiv)',
    wrong_label: 'Russian / Soviet',
  },
  Exter: {
    name:        'Alexandra Exter',
    true_label:  'Ukrainian-born (Kyiv)',
    wrong_label: 'Russian',
  },
  Pagava: {
    name:        'Vera Pagava',
    true_label:  'Georgian-born (Tbilisi)',
    wrong_label: 'Empire Russe',
  },
  Kakabadze: {
    name:        'David Kakabadze',
    true_label:  'Georgian-born (Kutaisi/Tbilisi)',
    wrong_label: 'Russian avant-garde',
  },
  Parajanov: {
    name:        'Sergei Parajanov',
    true_label:  'Soviet-Armenian (Georgian-born)',
    wrong_label: 'Soviet',
  },
};

// Misattribution type weights from dataset analysis
const MISATTRIBUTION_STATS = {
  parajanov: { total: 305, wrongLabel: 218, omission: 54, spelling: 33 },
  malevich:  { total: 272, wrongLabel: 195, omission: 61, spelling: 16 },
  exter:     { total: 44,  wrongLabel: 38,  omission: 4,  spelling: 2  },
  kakabadze: { total: 19,  wrongLabel: 0,   omission: 0,  structural: 19 },
  pagava:    { total: 19,  wrongLabel: 19,  omission: 0,  spelling: 0  },
};

// Key archives showing propagation
const ARCHIVE_CHAIN = [
  { name: 'Library of Congress', type: 'authority',  tier: 0 },
  { name: 'WorldCat / OCLC',     type: 'aggregator', tier: 1 },
  { name: 'Trove (NLA)',          type: 'national',   tier: 2 },
  { name: 'MoMA / NGA / NGV',    type: 'museum',     tier: 2 },
  { name: 'GPT / Claude / LLAMA',type: 'llm',        tier: 3 },
  { name: 'Google Knowledge',    type: 'web',        tier: 3 },
];

// State machine phases
const PHASES = {
  PRISTINE:     { id: 0, duration: 3500,  label: 'pristine'     },
  LABEL_APPLY:  { id: 1, duration: 3500,  label: 'label_apply'  },
  CORRUPT:      { id: 2, duration: 4500,  label: 'corrupt'      },
  PROPAGATE:    { id: 3, duration: 5000,  label: 'propagate'    },
  MACHINE_GAZE: { id: 4, duration: 4500,  label: 'machine_gaze' },
  INTERVENTION: { id: 5, duration: 3500,  label: 'intervention' },
  TRUTH:        { id: 6, duration: 6000,  label: 'truth'        },
  FADE:         { id: 7, duration: 2000,  label: 'fade'         },
};
const PHASE_ORDER = [0,1,2,3,4,5,6,7];
