// अभी future features डाल सकते हैं
console.log("Welcome Page Loaded");


// script.js
const buttons = document.querySelectorAll('.btn');

buttons.forEach(btn => {
  let angle = 45;
  setInterval(() => {
    angle += 1; // rotate gradient slowly
    btn.style.background = `linear-gradient(${angle}deg, #3D52A0, #7091E6)`;
  }, 50);
});
