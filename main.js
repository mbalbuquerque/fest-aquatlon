const menuToggle = document.getElementById("menuToggle");
const nav = document.querySelector(".nav");
menuToggle?.addEventListener("click", () => nav.classList.toggle("mobile"));

document.querySelectorAll("#mainNav a").forEach(link => {
  link.addEventListener("click", () => nav.classList.remove("mobile"));
});

const form = document.getElementById("registrationForm");
form?.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  localStorage.setItem("festAquathlonInscricaoDemo", JSON.stringify(data));
  alert(`Inscrição demonstrativa criada para ${data.nome}. Na próxima fase, estes dados serão enviados ao banco de dados e receberão um número de inscrição.`);
});

function showDemo(type) {
  const modal = document.getElementById("demoModal");
  document.getElementById("modalTitle").textContent = type;
  document.getElementById("modalText").textContent =
    type === "PIX" ? "Área reservada para QR Code e código PIX copia e cola."
    : type === "Cartão" ? "Área reservada para o botão/link do gateway de cartão."
    : "Área reservada para geração e acompanhamento do boleto.";
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");
}
function closeDemo() {
  const modal = document.getElementById("demoModal");
  modal.classList.remove("show");
  modal.setAttribute("aria-hidden", "true");
}
document.getElementById("demoModal")?.addEventListener("click", e => {
  if (e.target.id === "demoModal") closeDemo();
});
