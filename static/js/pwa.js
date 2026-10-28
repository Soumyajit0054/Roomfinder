if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}

let deferredPrompt = null;
const banner = document.getElementById("pwa-install");

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (banner && !sessionStorage.getItem("pwa-dismissed")) banner.style.display = "flex";
});

if (banner) {
  banner.querySelector("[data-install]").addEventListener("click", async () => {
    banner.style.display = "none";
    if (deferredPrompt) { deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; }
  });
  banner.querySelector("[data-dismiss]").addEventListener("click", () => {
    banner.style.display = "none";
    sessionStorage.setItem("pwa-dismissed", "1");
  });
}
