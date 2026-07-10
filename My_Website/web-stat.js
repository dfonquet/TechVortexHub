(function () {
  var accountId = 2217668;
  var trackerMode = 4;

  function loadWebStat() {
    var script = document.createElement("script");

    script.async = true;
    script.src = "https://app.ardalio.com/wts7.js";
    script.onload = function () {
      if (typeof window.wtsl7 === "function") {
        window.wtsl7(accountId, trackerMode);
      }
    };

    document.head.appendChild(script);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadWebStat);
    return;
  }

  loadWebStat();
})();
