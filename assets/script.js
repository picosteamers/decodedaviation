(function () {
  "use strict";

  var accordion = document.querySelector("[data-accordion]");
  if (accordion) {
    accordion.addEventListener("click", function (e) {
      var trigger = e.target.closest(".accordion-trigger");
      if (!trigger) return;
      var section = trigger.closest(".accordion-section");
      var panel = section.querySelector(".accordion-panel");
      var open = section.classList.toggle("open");
      panel.hidden = !open;
    });
  }

  var menuToggle = document.querySelector(".menu-toggle");
  var mainNav = document.querySelector(".main-nav");
  if (menuToggle && mainNav) {
    menuToggle.addEventListener("click", function () {
      mainNav.classList.toggle("nav-open");
    });
  }

  // Case-page location maps (Leaflet + OpenStreetMap, no API key).
  // Leaflet loads from an external CDN script tag; wait for the window
  // "load" event rather than assuming script-tag order guarantees it has
  // already run by the time this file executes.
  var mapEls = document.querySelectorAll(".case-map[data-lat]");
  if (mapEls.length) {
    window.addEventListener("load", function () {
      if (typeof L === "undefined") return;
      var maps = {};

      var initMap = function (el) {
        if (!el || maps[el.id]) return maps[el.id];
        var lat = parseFloat(el.dataset.lat);
        var lon = parseFloat(el.dataset.lon);
        if (isNaN(lat) || isNaN(lon)) return;
        var zoom = parseInt(el.dataset.zoom, 10) || 14;
        var map = L.map(el, { zoomControl: false, attributionControl: true }).setView([lat, lon], zoom);
        L.tileLayer("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        L.marker([lat, lon]).addTo(map);
        maps[el.id] = map;
        return map;
      };

      mapEls.forEach(initMap);

      window.addEventListener("resize", function () {
        Object.keys(maps).forEach(function (id) { maps[id].invalidateSize(); });
      });

      if (accordion) {
        accordion.addEventListener("click", function (e) {
          if (!e.target.closest(".accordion-trigger")) return;
          setTimeout(function () {
            Object.keys(maps).forEach(function (id) {
              var el = document.getElementById(id);
              if (el && el.offsetParent !== null) maps[id].invalidateSize();
            });
          }, 0);
        });
      }
    });
  }
})();
