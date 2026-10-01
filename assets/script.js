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
})();
