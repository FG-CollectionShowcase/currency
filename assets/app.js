(() => {
  const q = document.getElementById("q");
  if (!q) return;
  const country = document.getElementById("country");
  const metal = document.getElementById("metal");
  const flag = document.getElementById("flag");
  const type = document.getElementById("type");
  const shown = document.getElementById("shown");
  const items = [...document.querySelectorAll(".pocket[data-text], #tbl tbody tr")];

  function apply() {
    const words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    let n = 0;
    for (const el of items) {
      const d = el.dataset;
      const ok = words.every(w => d.text.includes(w)) &&
        (!country.value || d.country === country.value) &&
        (!metal.value || d.metal === metal.value) &&
        (!type.value || d.type === type.value) &&
        (!flag.checked || d.flag === "1");
      el.classList.toggle("hide", !ok);
      if (ok && el.tagName === "TR") n++;
    }
    const total = document.querySelectorAll("#tbl tbody tr").length;
    shown.textContent = n === total ? "" : `${n} of ${total} shown`;
  }
  [q, country, metal, type, flag].forEach(el => el.addEventListener("input", apply));

  // sortable table
  const tbody = document.querySelector("#tbl tbody");
  document.querySelectorAll("#tbl th").forEach((th, i) => {
    th.addEventListener("click", () => {
      const asc = !th.classList.contains("asc");
      document.querySelectorAll("#tbl th").forEach(h => h.classList.remove("asc", "desc"));
      th.classList.add(asc ? "asc" : "desc");
      const key = r => { const c = r.children[i]; return c.dataset.v !== undefined ? parseFloat(c.dataset.v) : c.textContent.trim().toLowerCase(); };
      [...tbody.rows].sort((a, b) => { const x = key(a), y = key(b); return (x > y ? 1 : x < y ? -1 : 0) * (asc ? 1 : -1); })
        .forEach(r => tbody.appendChild(r));
    });
  });
})();
