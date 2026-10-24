/**
 * LifeCard PS-40 - Client Interaction Script (Vanilla JS)
 */

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initFlipCard();
  initConsentToggles();
  initPolling();
  initDoctorScanner();
  initCountdown();
  initPresetChips();
  initLocationSharer();
});

// Toast notification helper
function showToast(message, isAlert = false) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast" + (isAlert ? " toast-alert" : "");
  toast.innerHTML = `
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;cursor:pointer;font-size:1.1rem;line-height:1;">&times;</button>
  `;

  container.appendChild(toast);

  if (isAlert) {
    if ("vibrate" in navigator) {
      try { navigator.vibrate([200, 100, 200]); } catch (e) {}
    }
  }

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Tabs
function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  if (!tabButtons.length) return;

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      const parent = btn.closest(".tabs-wrapper") || document;

      parent.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      parent.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetEl = parent.querySelector(`#tab-${target}`);
      if (targetEl) targetEl.classList.add("active");
    });
  });
}

// 3D Flip Card
function initFlipCard() {
  const flipCard = document.getElementById("lifeCard3D");
  if (!flipCard) return;

  flipCard.addEventListener("click", () => {
    flipCard.classList.toggle("is-flipped");
  });

  const flipBtn = document.getElementById("flipCardBtn");
  if (flipBtn) {
    flipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      flipCard.classList.toggle("is-flipped");
    });
  }
}

// Privacy Consent Toggles with instant iframe refresh
function initConsentToggles() {
  const toggles = document.querySelectorAll(".consent-toggle");
  if (!toggles.length) return;

  const previewFrame = document.getElementById("helperPreviewFrame");

  toggles.forEach(toggle => {
    toggle.addEventListener("change", async () => {
      const field = toggle.name;
      const val = toggle.checked ? 1 : 0;

      try {
        const res = await fetch("/api/consent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: val })
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`Privacy setting updated for ${field.replace('share_', '')}`);
          if (previewFrame) {
            // Reload iframe with cache buster
            const currentSrc = previewFrame.src.split('&_t=')[0];
            previewFrame.src = `${currentSrc}&_t=${Date.now()}`;
          }
        }
      } catch (err) {
        console.error("Failed to update consent:", err);
        showToast("Error updating privacy setting", true);
      }
    });
  });
}

// Polling for Family and Patient Feeds
let lastEventId = null;

function initPolling() {
  const familyTimeline = document.getElementById("familyTimeline");
  const patientTimeline = document.getElementById("patientTimeline");

  if (familyTimeline) {
    // Request notification permission if available
    if ("Notification" in window && Notification.permission === "default") {
      document.body.addEventListener("click", () => {
        Notification.requestPermission();
      }, { once: true });
    }

    setInterval(() => pollFeed("family", updateFamilyUI), 3000);
  }

  if (patientTimeline) {
    setInterval(() => pollFeed("patient", updatePatientUI), 4000);
  }
}

async function pollFeed(scope, callback) {
  try {
    const res = await fetch(`/api/feed?scope=${scope}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.events && data.events.length > 0) {
      callback(data.events, data);
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}

function updateFamilyUI(events, meta) {
  const familyTimeline = document.getElementById("familyTimeline");
  if (!familyTimeline) return;

  const latest = events[0];
  if (lastEventId !== null && latest && latest.id > lastEventId) {
    // Trigger Alert!
    showToast(`🚨 New Alert: ${latest.text || latest.kind}`, true);
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("LifeCard Emergency Alert", {
        body: latest.text || "New scan detected for Asha Sharma",
        icon: "/static/avatars/asha.png"
      });
    }
  }
  if (latest) {
    lastEventId = latest.id;
  }

  // Update status banner
  const banner = document.getElementById("familyStatusBanner");
  if (banner && meta.status) {
    banner.className = `status-banner ${meta.status.cls}`;
    banner.innerHTML = `
      <div>
        <h3 style="font-size:1.1rem;margin-bottom:2px;">${meta.status.title}</h3>
        <p style="font-size:0.85rem;opacity:0.9;">${meta.status.subtitle}</p>
      </div>
      <span class="badge ${meta.status.badgeCls}">${meta.status.badgeText}</span>
    `;
  }

  // Update journey tracker
  if (meta.journey) {
    for (let step = 1; step <= 4; step++) {
      const stepEl = document.getElementById(`journeyStep${step}`);
      if (stepEl) {
        if (meta.journey.current >= step) {
          stepEl.className = "journey-step completed";
        } else if (meta.journey.current === step - 1) {
          stepEl.className = "journey-step active";
        } else {
          stepEl.className = "journey-step";
        }
      }
    }
  }

  // Update embedded map if lat/lng available
  const mapFrame = document.getElementById("familyMapFrame");
  const mapLink = document.getElementById("familyMapLink");
  if (mapFrame && meta.map_location) {
    const newSrc = `https://maps.google.com/maps?q=${meta.map_location.lat},${meta.map_location.lng}&z=16&output=embed`;
    if (!mapFrame.src.includes(`${meta.map_location.lat},${meta.map_location.lng}`)) {
      mapFrame.src = newSrc;
    }
    if (mapLink) {
      mapLink.href = `https://www.google.com/maps/search/?api=1&query=${meta.map_location.lat},${meta.map_location.lng}`;
      mapLink.style.display = "inline-flex";
    }
  }

  // Re-render timeline events
  renderTimeline(familyTimeline, events);
}

function updatePatientUI(events) {
  const patientTimeline = document.getElementById("patientTimeline");
  if (!patientTimeline) return;
  renderTimeline(patientTimeline, events);
}

function renderTimeline(container, events) {
  if (!events || events.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🛡️</div><p>No activity logged yet.</p></div>`;
    return;
  }

  container.innerHTML = events.map(e => `
    <div class="timeline-item">
      <div class="timeline-icon">${e.icon}</div>
      <div class="timeline-content">
        <div class="timeline-meta">
          <span style="font-weight:700;color:var(--navy);">${e.title}</span>
          <span>${e.time_ago} (${e.time_ist})</span>
        </div>
        <p style="font-size:0.9rem;margin-bottom:4px;">${e.text || ''}</p>
        ${e.maps_url ? `<a href="${e.maps_url}" target="_blank" rel="noopener" style="font-size:0.8rem;color:var(--teal);text-decoration:none;font-weight:600;">📍 Open Shared Location</a>` : ''}
      </div>
    </div>
  `).join("");
}

// Doctor BarcodeDetector + getUserMedia camera scanner
function initDoctorScanner() {
  const startScanBtn = document.getElementById("startCameraScanBtn");
  const scannerVideo = document.getElementById("scannerVideo");
  const fallbackMsg = document.getElementById("scannerFallbackMsg");

  if (!startScanBtn || !scannerVideo) return;

  startScanBtn.addEventListener("click", async () => {
    if (!("BarcodeDetector" in window)) {
      if (fallbackMsg) {
        fallbackMsg.style.display = "block";
        fallbackMsg.innerText = "BarcodeDetector is not supported in this browser. Please use the 'Simulate scan' button below.";
      }
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }
      });
      scannerVideo.srcObject = stream;
      scannerVideo.style.display = "block";
      startScanBtn.style.display = "none";
      if (fallbackMsg) fallbackMsg.style.display = "none";

      const barcodeDetector = new BarcodeDetector({ formats: ["qr_code"] });
      const scanLoop = async () => {
        if (!scannerVideo.srcObject) return;
        try {
          const barcodes = await barcodeDetector.detect(scannerVideo);
          if (barcodes.length > 0) {
            const raw = barcodes[0].rawValue;
            // Stop stream and redirect
            stream.getTracks().forEach(t => t.stop());
            window.location.href = raw;
            return;
          }
        } catch (e) {}
        requestAnimationFrame(scanLoop);
      };
      scannerVideo.onloadedmetadata = () => {
        scannerVideo.play();
        scanLoop();
      };
    } catch (err) {
      console.warn("Camera access denied or failed:", err);
      if (fallbackMsg) {
        fallbackMsg.style.display = "block";
        fallbackMsg.innerText = "Camera access unavailable or permission denied. Please use the 'Simulate scan' button below.";
      }
    }
  });
}

// Countdown timer for doctor 30-minute session
function initCountdown() {
  const timerEl = document.getElementById("grantCountdownTimer");
  if (!timerEl) return;

  let secondsLeft = parseInt(timerEl.dataset.secondsLeft || "1800", 10);

  const update = () => {
    if (secondsLeft <= 0) {
      timerEl.innerText = "Access expired";
      timerEl.style.background = "var(--red-light)";
      timerEl.style.color = "var(--red)";
      setTimeout(() => window.location.reload(), 1500);
      return;
    }
    const mins = Math.floor(secondsLeft / 60);
    const secs = secondsLeft % 60;
    timerEl.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')} remaining`;
    secondsLeft--;
  };

  update();
  setInterval(update, 1000);
}

// Preset chips on doctor notes tab
function initPresetChips() {
  const chips = document.querySelectorAll(".preset-update-chip");
  const textarea = document.getElementById("doctorUpdateText");
  if (!chips.length || !textarea) return;

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      textarea.value = chip.dataset.text || chip.innerText.trim();
      textarea.focus();
    });
  });
}

// Helper page GPS location sharer
function initLocationSharer() {
  const shareBtn = document.getElementById("shareLocationBtn");
  const statusEl = document.getElementById("shareLocationStatus");
  if (!shareBtn) return;

  shareBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      if (statusEl) statusEl.innerText = "Geolocation is not supported by your browser.";
      return;
    }

    const eventId = shareBtn.dataset.eventId;
    const token = shareBtn.dataset.token;
    shareBtn.disabled = true;
    if (statusEl) statusEl.innerText = "Detecting high-accuracy GPS coordinates...";

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const res = await fetch(`/s/${token}/location`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              event_id: eventId,
              lat: latitude,
              lng: longitude
            })
          });
          const data = await res.json();
          if (data.ok) {
            if (statusEl) {
              statusEl.innerText = "✓ Location shared! Patient's family notified.";
              statusEl.style.color = "var(--teal-dark)";
            }
            shareBtn.innerText = "✓ Location Shared";
            shareBtn.classList.add("btn-teal");
            shareBtn.classList.remove("btn-outline");

            // Update nearest hospital button if present
            const hospBtn = document.getElementById("findHospitalBtn");
            if (hospBtn) {
              hospBtn.href = `https://www.google.com/maps/search/hospitals/@${latitude},${longitude},14z`;
            }
          } else {
            if (statusEl) statusEl.innerText = "Failed to update location.";
            shareBtn.disabled = false;
          }
        } catch (e) {
          if (statusEl) statusEl.innerText = "Network error sharing location.";
          shareBtn.disabled = false;
        }
      },
      (err) => {
        if (statusEl) statusEl.innerText = `Location access denied (${err.message}).`;
        shareBtn.disabled = false;
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  });
}
