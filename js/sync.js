// ─────────────────────────────────────────────────────────────────────────────
// Multi-screen synchronisation
// All browser instances share phase timing via localStorage (same machine)
// or via the server's /api/sync endpoint (across machines on a network).
//
// Each screen writes nothing; the curator / lead screen (screen=1) drives the
// clock and all other screens read it. Fallback: each screen runs independently
// if no sync signal is received within 3 seconds.
// ─────────────────────────────────────────────────────────────────────────────

const SYNC_KEY       = 'misattribution_sync';
const SYNC_INTERVAL  = 500;   // ms — how often to write/read sync state
const SYNC_TIMEOUT   = 3000;  // ms — fall back to independent if no signal

let syncState = null;
let lastSyncRead = 0;
let syncLeader = false;  // true only on screen 1

function initSync() {
  const screenId = screenCfg.id;
  syncLeader = (screenId === 1);

  if (syncLeader) {
    // Leader writes state
    setInterval(writeSync, SYNC_INTERVAL);
  } else {
    // Followers poll storage
    setInterval(readSync, SYNC_INTERVAL);
  }
}

function writeSync() {
  const payload = JSON.stringify({
    phaseIndex:  phaseIndex,
    artist:      state.artist,
    phaseStart:  state.phaseStart,
    ts:          Date.now(),
  });
  try {
    localStorage.setItem(SYNC_KEY, payload);
  } catch (_) {}
}

function readSync() {
  try {
    const raw = localStorage.getItem(SYNC_KEY);
    if (!raw) return;
    const s = JSON.parse(raw);
    if (Date.now() - s.ts > SYNC_TIMEOUT) return;  // stale — run independently

    // Apply sync if we're behind or ahead by more than half a phase
    if (s.phaseIndex !== phaseIndex) {
      phaseIndex       = s.phaseIndex;
      const phases     = Object.values(PHASES);
      state.phase      = phases[PHASE_ORDER[phaseIndex]];
      state.phaseStart = s.phaseStart;
    }
    if (s.artist !== state.artist) {
      currentArtist = s.artist;
      state = buildState(s.artist);
      phaseIndex = 0;
      initParticles();
      initArchiveNodes();
    }
    lastSyncRead = Date.now();
  } catch (_) {}
}

// Server-side sync (when screens are on separate machines)
async function fetchServerSync() {
  try {
    const res  = await fetch('/api/sync');
    const data = await res.json();
    if (data.artist && data.phaseIndex !== undefined) {
      if (data.artist !== state.artist || data.phaseIndex !== phaseIndex) {
        currentArtist    = data.artist;
        phaseIndex       = data.phaseIndex;
        state            = buildState(data.artist);
        const phases     = Object.values(PHASES);
        state.phase      = phases[PHASE_ORDER[phaseIndex]];
        state.phaseStart = millis() - data.elapsedMs;
        initParticles();
        initArchiveNodes();
      }
    }
  } catch (_) {}
}
