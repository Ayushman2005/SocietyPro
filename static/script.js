document.addEventListener("DOMContentLoaded", () => {
  // --- 1. DYNAMIC SEARCH BAR (Admin & User Dashboards) ---
  // Automatically injects a search bar into the dashboard header
  const dashboardHeader = document.querySelector(".header");
  const cardsContainer = document.querySelector(".cards");

  if (dashboardHeader && cardsContainer) {
    // Create Search Input
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "🔍 Search bills...";
    searchInput.style.padding = "8px 15px";
    searchInput.style.borderRadius = "20px";
    searchInput.style.border = "1px solid var(--border-color)";
    searchInput.style.marginLeft = "15px";
    searchInput.style.outline = "none";
    searchInput.style.fontSize = "14px";
    searchInput.style.color = "var(--text-white)";
    searchInput.style.backgroundColor = "var(--bg-input)";

    // Insert after the Title
    const title = dashboardHeader.querySelector("h2");
    title.parentNode.insertBefore(searchInput, title.nextSibling);

    // Filter Logic
    searchInput.addEventListener("keyup", (e) => {
      const term = e.target.value.toLowerCase();
      const cards = document.querySelectorAll(".card");

      cards.forEach((card) => {
        const text = card.textContent.toLowerCase();
        if (text.includes(term)) {
          card.style.display = text.includes(term) ? "block" : "none";
          // Re-apply animation for filtered items
          card.style.animation = "fadeIn 0.5s ease forwards";
        } else {
          card.style.display = "none";
        }
      });
    });
  }

  // --- 2. SHOW/HIDE PASSWORD TOGGLE (Login Pages) ---
  const passwordInputs = document.querySelectorAll('input[type="password"]');

  passwordInputs.forEach((input) => {
    // Create wrapper to position the eye icon
    const wrapper = document.createElement("div");
    wrapper.style.position = "relative";
    wrapper.style.width = "100%";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    // Create the Toggle Button (Eye Icon)
    const toggleBtn = document.createElement("span");
    toggleBtn.innerHTML = "👁️";
    toggleBtn.style.position = "absolute";
    toggleBtn.style.right = "15px";
    toggleBtn.style.top = "50%";
    toggleBtn.style.transform = "translateY(-50%)";
    toggleBtn.style.cursor = "pointer";
    toggleBtn.style.opacity = "0.7";
    toggleBtn.style.fontSize = "18px";
    toggleBtn.style.userSelect = "none";
    toggleBtn.title = "Show Password";

    wrapper.appendChild(toggleBtn);

    toggleBtn.addEventListener("click", () => {
      if (input.type === "password") {
        input.type = "text";
        toggleBtn.style.opacity = "0.6"; // Dimmed when visible
      } else {
        input.type = "password";
        toggleBtn.style.opacity = "1";
      }
    });
  });

  // --- 3. SCROLL REVEAL ANIMATION (Landing Page) ---
  // Uses Intersection Observer to fade in elements when they scroll into view
  const observerOptions = {
    threshold: 0.15, // Trigger when 15% of element is visible
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target); // Only animate once
      }
    });
  }, observerOptions);

  const scrollElements = document.querySelectorAll(
    ".feature-card, .hero-content, .hero-image"
  );

  // Inject CSS for the animation dynamically
  const style = document.createElement("style");
  style.innerHTML = `
        .feature-card, .hero-content, .hero-image {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s ease-out;
        }
        .feature-card.visible, .hero-content.visible, .hero-image.visible {
            opacity: 1;
            transform: translateY(0);
        }
        /* Ripple Effect CSS */
        .ripple {
            position: absolute;
            background: rgba(255, 255, 255, 0.4);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        /* Make buttons relative for ripple */
        button, .btn-primary, .login-btn {
            position: relative;
            overflow: hidden;
        }
    `;
  document.head.appendChild(style);

  scrollElements.forEach((el) => observer.observe(el));
  document.addEventListener("DOMContentLoaded", () => {
    // --- 1. NUMBER COUNTING ANIMATION ---
    const counters = document.querySelectorAll(".stat-number");
    const speed = 200; // The lower the slower

    const animateCounters = () => {
      counters.forEach((counter) => {
        const updateCount = () => {
          const target = +counter.getAttribute("data-target");
          const count = +counter.innerText;
          const inc = target / speed;

          if (count < target) {
            counter.innerText = Math.ceil(count + inc);
            setTimeout(updateCount, 20);
          } else {
            counter.innerText = target + "+"; // Append + at the end
          }
        };
        updateCount();
      });
    };

    // Trigger animation when stats section is in view
    const statsSection = document.querySelector(".stats-banner");
    if (statsSection) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              animateCounters();
              observer.unobserve(statsSection);
            }
          });
        },
        { threshold: 0.5 }
      );
      observer.observe(statsSection);
    }

    // --- 2. CONTACT FORM HANDLER ---
    const contactForm = document.querySelector(".footer-form");
    if (contactForm) {
      contactForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const btn = contactForm.querySelector("button");
        const originalText = btn.innerText;

        // Simulation of sending
        btn.innerText = "Sending...";
        btn.style.opacity = "0.7";

        setTimeout(() => {
          alert("Thank you! Your message has been sent to our support team.");
          contactForm.reset();
          btn.innerText = originalText;
          btn.style.opacity = "1";
        }, 1500);
      });
    }
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute("href")).scrollIntoView({
          behavior: "smooth",
        });
      });
    });
  });
  // --- 4. BUTTON RIPPLE EFFECT ---
  const buttons = document.querySelectorAll("button, .btn-primary, .login-btn");

  buttons.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      const circle = document.createElement("span");
      const diameter = Math.max(btn.clientWidth, btn.clientHeight);
      const radius = diameter / 2;

      // Calculate click position relative to button
      const rect = btn.getBoundingClientRect();
      circle.style.width = circle.style.height = `${diameter}px`;
      circle.style.left = `${e.clientX - rect.left - radius}px`;
      circle.style.top = `${e.clientY - rect.top - radius}px`;
      circle.classList.add("ripple");

      // Remove existing ripple if any
      const existingRipple = btn.querySelector(".ripple");
      if (existingRipple) {
        existingRipple.remove();
      }

      btn.appendChild(circle);
    });
  });

  // --- 5. LOGOUT CONFIRMATION (Existing Logic) ---
  const logoutBtn = document.querySelector(".logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      if (!confirm("Are you sure you want to log out?")) {
        e.preventDefault();
      }
    });
  }

  // --- 6. ADMIN FORM VALIDATION (Existing Logic) ---
  const addBillForm = document.querySelector('form[action="/admin/add_bill"]');
  if (addBillForm) {
    addBillForm.addEventListener("submit", (e) => {
      const amountInput = addBillForm.querySelector('input[name="amount"]');
      const userIdInput = addBillForm.querySelector('input[name="user_id"]');

      if (
        parseFloat(amountInput.value) <= 0 ||
        parseInt(userIdInput.value) <= 0
      ) {
        e.preventDefault();
        alert("Error: Amount and User ID must be positive numbers.");
      }
    });
  }
  // --- 0. THEME TOGGLE LOGIC ---
  const themeBtn = document.getElementById("theme-toggle");
  const body = document.body;
  const icon = themeBtn ? themeBtn.querySelector("i") : null;

  // 1. Check LocalStorage on Load
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme === "light") {
    body.classList.add("light-mode");
    if(icon) icon.className = "ri-moon-line"; // Show Moon icon in light mode
  }

  // 2. Button Click Event
  if (themeBtn) {
    themeBtn.addEventListener("click", (e) => {
      e.preventDefault(); // Prevent link jump
      body.classList.toggle("light-mode");

      // Update Icon & Save Preference
      if (body.classList.contains("light-mode")) {
        localStorage.setItem("theme", "light");
        if(icon) icon.className = "ri-moon-line";
      } else {
        localStorage.setItem("theme", "dark");
        if(icon) icon.className = "ri-sun-line";
      }
    });
  }
});
