// Motion: soft staggered reveals, eased count-ups, self-drawing gauge, bar fills.
(function () {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const easeOutExpo = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));

  // --- count-up: [data-count] (target), data-decimals, data-suffix ---
  function countUp(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    const target = parseFloat(el.dataset.count);
    const dec = parseInt(el.dataset.decimals || "0", 10);
    const suffix = el.dataset.suffix || "";
    if (reduce || isNaN(target)) {
      el.textContent = (isNaN(target) ? "0" : target.toFixed(dec)) + suffix;
      return;
    }
    const dur = 1400;
    let start = null;
    function frame(ts) {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / dur, 1);
      const v = target * easeOutExpo(p);
      el.textContent = v.toFixed(dec) + suffix;
      if (p < 1) requestAnimationFrame(frame);
      else el.textContent = target.toFixed(dec) + suffix;
    }
    requestAnimationFrame(frame);
  }

  // --- gauge: stroke draws to (1 - score/100) of circumference ---
  function drawGauge(circle) {
    if (circle.dataset.done) return;
    circle.dataset.done = "1";
    const r = circle.r.baseVal.value;
    const circ = 2 * Math.PI * r;
    const score = Math.max(0, Math.min(100, parseFloat(circle.dataset.score) || 0));
    circle.style.strokeDasharray = circ.toFixed(2);
    circle.style.strokeDashoffset = circ.toFixed(2); // start empty
    const target = circ * (1 - score / 100);
    if (reduce) { circle.style.transition = "none"; circle.style.strokeDashoffset = target.toFixed(2); return; }
    requestAnimationFrame(() => requestAnimationFrame(() => {
      circle.style.strokeDashoffset = target.toFixed(2);
    }));
  }

  // --- bar / mini-bar fill from data-w (percent) ---
  function fillBar(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    const w = Math.max(0, Math.min(100, parseFloat(el.dataset.w) || 0));
    requestAnimationFrame(() => requestAnimationFrame(() => { el.style.width = w + "%"; }));
  }

  // run all animations contained in a (now-visible) element
  function animateWithin(root) {
    root.querySelectorAll("[data-count]").forEach(countUp);
    root.querySelectorAll(".gauge-fill").forEach(drawGauge);
    root.querySelectorAll("[data-w]").forEach(fillBar);
  }

  // --- reveal orchestration ---
  const io = "IntersectionObserver" in window
    ? new IntersectionObserver((entries, obs) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            animateWithin(e.target);
            obs.unobserve(e.target);
          }
        });
      }, { threshold: 0.18, rootMargin: "0px 0px -8% 0px" })
    : null;

  document.addEventListener("DOMContentLoaded", () => {
    const reveals = Array.from(document.querySelectorAll(".reveal"));
    reveals.forEach((el, i) => { if (el.style.getPropertyValue("--i") === "") el.style.setProperty("--i", i % 8); });

    if (io) {
      reveals.forEach((el) => io.observe(el));
      // kick anything already in view on load (hero) immediately
      reveals.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight * 0.92) { el.classList.add("in"); animateWithin(el); io.unobserve(el); }
      });
    } else {
      reveals.forEach((el) => { el.classList.add("in"); animateWithin(el); });
    }

    // --- dropzone interactions ---
    const drop = document.querySelector(".drop");
    if (drop) {
      const input = drop.querySelector('input[type=file]');
      const chosen = drop.querySelector(".chosen");
      const btn = document.querySelector(".btn-analyze");
      ["dragenter", "dragover"].forEach((ev) =>
        drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("dragover"); }));
      ["dragleave", "drop"].forEach((ev) =>
        drop.addEventListener(ev, (e) => { e.preventDefault(); if (ev === "dragleave" && drop.contains(e.relatedTarget)) return; drop.classList.remove("dragover"); }));
      drop.addEventListener("drop", (e) => { if (e.dataTransfer.files.length) input.files = e.dataTransfer.files; sync(); });
      input.addEventListener("change", sync);
      function sync() {
        const f = input.files && input.files[0];
        if (f) { chosen.textContent = "› " + f.name; if (btn) btn.disabled = false; }
        else { chosen.textContent = ""; if (btn) btn.disabled = true; }
      }
      sync();
    }
  });
})();
