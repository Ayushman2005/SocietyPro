document.addEventListener("DOMContentLoaded", () => {
  // Inject mouse glowing blob
  const glow = document.createElement("div");
  glow.className = "glow-blob";
  document.body.appendChild(glow);

  document.addEventListener("mousemove", (e) => {
    glow.style.left = `${e.clientX}px`;
    glow.style.top = `${e.clientY}px`;
    glow.style.opacity = "1";
  });

  document.addEventListener("mouseleave", () => {
    glow.style.opacity = "0";
  });

  // Navbar scrolled effect
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
      } else {
        navbar.classList.remove("scrolled");
      }
    });
  }

  const cards = document.querySelectorAll(
    ".card, .feature-box, .hero-image img",
  );

  cards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -5; // Max 5deg tilt
      const rotateY = ((x - centerX) / centerX) * 5;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform =
        "perspective(1000px) rotateX(0) rotateY(0) scale(1)";
    });
  });
  const counters = document.querySelectorAll(".stat-number"); // Removed .card-amount to prevent currency mangle
  counters.forEach((counter) => {
    const target = +counter.innerText.replace(/[^0-9.]/g, ""); // Extract number but keep decimal
    if (target > 0) {
      let count = 0;
      const increment = target / 50;
      const updateCount = () => {
        count += increment;
        if (count < target) {
          counter.innerText = Math.ceil(count);
          requestAnimationFrame(updateCount);
        } else {
          counter.innerText = target;
        }
      };
      updateCount();
    }
  });
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1 },
  );

  document
    .querySelectorAll(".feature-card, .card, .table-box")
    .forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(30px)";
      el.style.transition = "all 0.6s ease-out";
      observer.observe(el);
    });
  const hamburger = document.querySelector(".hamburger");
  const navLinks = document.querySelector(".nav-links");
  if (hamburger) {
    hamburger.addEventListener("click", () => {
      navLinks.classList.toggle("active");
    });
  }
  const dashContainer = document.querySelector(".dashboard-container");
  const sidebar = document.querySelector(".sidebar");
  if (!dashContainer || !sidebar) return;
  const topBar = document.createElement("div");
  topBar.id = "mobile-topbar";
  topBar.innerHTML = `
    <div id="mob-logo">${sidebar.querySelector(".logo") ? sidebar.querySelector(".logo").innerHTML : "☰ Menu"}</div>
    <button id="mob-hamburger" aria-label="Open navigation menu" aria-expanded="false">
      <span class="ham-line"></span>
      <span class="ham-line"></span>
      <span class="ham-line"></span>
    </button>
  `;
  document.body.prepend(topBar);
  const overlay = document.createElement("div");
  overlay.id = "sidebar-overlay";
  document.body.appendChild(overlay);

  const mobBtn = document.getElementById("mob-hamburger");

  function openDrawer() {
    sidebar.classList.add("drawer-open");
    overlay.classList.add("overlay-visible");
    mobBtn.classList.add("is-open");
    mobBtn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    sidebar.classList.remove("drawer-open");
    overlay.classList.remove("overlay-visible");
    mobBtn.classList.remove("is-open");
    mobBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  mobBtn.addEventListener("click", () => {
    sidebar.classList.contains("drawer-open") ? closeDrawer() : openDrawer();
  });

  overlay.addEventListener("click", closeDrawer);
  sidebar.querySelectorAll(".menu a, .logout-btn").forEach((link) => {
    link.addEventListener("click", closeDrawer);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });
});