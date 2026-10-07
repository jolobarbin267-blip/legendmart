// LegendMart - main.js
// Typewriter + mobile menu + 3D tilt + copy-to-clipboard

// 1. TYPEWRITER
const words = ["MYTHIC account.", "Legendary skin.", "high-rank account.", "rare skin account."];
let wordIndex = 0, charIndex = 0, isDeleting = false;
const typeSpeed = 90, deleteSpeed = 45, pauseTime = 1500;
const typewriterEl = document.getElementById("typewriter");

function typeLoop() {
  if (!typewriterEl) return;
  const currentWord = words[wordIndex];
  if (isDeleting) {
    typewriterEl.textContent = currentWord.substring(0, charIndex - 1);
    charIndex--;
  } else {
    typewriterEl.textContent = currentWord.substring(0, charIndex + 1);
    charIndex++;
  }
  let delay = isDeleting ? deleteSpeed : typeSpeed;
  if (!isDeleting && charIndex === currentWord.length) { delay = pauseTime; isDeleting = true; }
  else if (isDeleting && charIndex === 0) { isDeleting = false; wordIndex = (wordIndex + 1) % words.length; delay = 400; }
  setTimeout(typeLoop, delay);
}
document.addEventListener("DOMContentLoaded", typeLoop);

// 2. MOBILE MENU
const hamburger = document.getElementById("hamburger");
const navLinks = document.getElementById("navLinks");
if (hamburger && navLinks) {
  hamburger.addEventListener("click", () => navLinks.classList.toggle("active"));
  document.querySelectorAll(".nav-link, .nav-btns .btn").forEach(link => {
    link.addEventListener("click", () => navLinks.classList.remove("active"));
  });
}

// 3. 3D TILT
document.querySelectorAll("[data-tilt]").forEach(el => {
  const inner = el.firstElementChild;
  el.addEventListener("mousemove", (e) => {
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -10;
    const rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 10;
    if (inner) inner.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  });
  el.addEventListener("mouseleave", () => { if (inner) inner.style.transform = "rotateX(0) rotateY(0)"; });
});

// 4. COPY TO CLIPBOARD (payment numbers)
document.querySelectorAll(".copy-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const text = btn.getAttribute("data-copy");
    if (!text) return;
    const done = () => {
      const original = btn.textContent;
      btn.textContent = "Copied!";
      btn.classList.add("copy-success");
      setTimeout(() => { btn.textContent = original; btn.classList.remove("copy-success"); }, 2000);
    };
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(done).catch(() => {
        const ta = document.createElement("textarea");
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand("copy"); document.body.removeChild(ta); done();
      });
    } else { done(); }
  });
});
