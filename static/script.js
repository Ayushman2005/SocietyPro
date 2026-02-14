document.addEventListener("DOMContentLoaded", () => {
  // --- 1. 3D TILT EFFECT FOR CARDS ---
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

  // --- 2. NUMBER COUNTER ANIMATION ---
  const counters = document.querySelectorAll(".stat-number, .card-amount");
  counters.forEach((counter) => {
    const target = +counter.innerText.replace(/[^0-9]/g, ""); // Extract number
    if (target > 0) {
      let count = 0;
      const increment = target / 50; // Speed
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

  // --- 3. SCROLL REVEAL ---
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

  // --- 4. MOBILE MENU ---
  const hamburger = document.querySelector(".hamburger");
  const navLinks = document.querySelector(".nav-links");
  if (hamburger) {
    hamburger.addEventListener("click", () => {
      navLinks.classList.toggle("active");
      // Simple toggle logic for mobile
      if (navLinks.style.display === "flex") navLinks.style.display = "none";
      else {
        navLinks.style.display = "flex";
        navLinks.style.flexDirection = "column";
        navLinks.style.position = "absolute";
        navLinks.style.top = "80px";
        navLinks.style.right = "20px";
        navLinks.style.background = "#111";
        navLinks.style.padding = "20px";
        navLinks.style.borderRadius = "12px";
      }
    });
  }
  
});
