document.addEventListener("click", function (event) {
  if (!event.target || event.target.id !== "clear_agent") return;
  if (!window.Shiny) return;
  Shiny.setInputValue("report_html", "", { priority: "event" });
});
