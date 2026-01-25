let isYearly = false;

const freePrice = document.getElementById("price-free");
const standardPrice = document.getElementById("price-standard");
const premiumPrice = document.getElementById("price-premium");

const toggleBtn = document.getElementById("toggleBtn");
const toggleKnob = document.getElementById("toggleKnob");

toggleBtn.addEventListener("click", () => {
  isYearly = !isYearly;

  // Remove both first
  toggleKnob.classList.remove("toggle-on", "toggle-off");

  // Then add the correct one
  if (isYearly) {
    toggleKnob.classList.add("toggle-on");

    freePrice.innerText = "$ 0 /year";
    standardPrice.innerText = "$ 99.9/year";
    premiumPrice.innerText = "$ 199.99 /year";
  } else {
    toggleKnob.classList.add("toggle-off");

    freePrice.innerText = "$ 0 /month";
    standardPrice.innerText = "$ 9.99/month";
    premiumPrice.innerText = "$ 19.99/month";
  }
});
