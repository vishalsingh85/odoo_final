function togglePassword(inputId, eyeIcon) {
  const input = document.getElementById(inputId);
  if (input.type === "password") {
    input.type = "text";
    eyeIcon.textContent = "🙈";
  } else {
    input.type = "password";
    eyeIcon.textContent = "👁️";
  }
}
