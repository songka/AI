(function () {
  "use strict";
  const data = window.AI_ASSETS_HUB_DATA;
  const list = document.getElementById("asset-list");
  const empty = document.getElementById("empty");
  const query = document.getElementById("query");
  const filters = document.getElementById("filters");
  let selected = "all";

  if (!data) {
    document.getElementById("freshness").textContent = "缺少 hub-data.js";
    empty.hidden = false;
    empty.textContent = "数据尚未生成。请由管理员运行 web-export。";
    return;
  }

  document.getElementById("package-count").textContent = data.counts.packages;
  document.getElementById("release-count").textContent = data.counts.releases;
  document.getElementById("dependency-count").textContent = data.counts.dependencies;
  document.getElementById("generation").textContent = data.generation ?? "—";
  document.getElementById("exported-at").textContent = `数据导出：${new Date(data.exportedAt).toLocaleString()}`;
  document.getElementById("freshness").textContent = `本地数据 · ${new Date(data.exportedAt).toLocaleString()}`;

  const types = ["all", ...new Set(data.packages.map(item => item.id.split("/")[0]))];
  types.forEach(type => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = type === "all" ? "全部" : type.toUpperCase();
    button.className = type === selected ? "active" : "";
    button.addEventListener("click", () => {
      selected = type;
      [...filters.children].forEach(item => item.classList.remove("active"));
      button.classList.add("active");
      render();
    });
    filters.appendChild(button);
  });

  function safe(value) {
    const node = document.createElement("span");
    node.textContent = value == null ? "" : String(value);
    return node.innerHTML;
  }

  function render() {
    const term = query.value.trim().toLowerCase();
    const packages = data.packages.filter(item => {
      const type = item.id.split("/")[0];
      const haystack = JSON.stringify(item).toLowerCase();
      return (selected === "all" || selected === type) && (!term || haystack.includes(term));
    });
    list.innerHTML = packages.map(item => {
      const type = item.id.split("/")[0];
      const releases = item.releases.map(release => {
        const deps = release.dependencies.length
          ? release.dependencies.map(dep => `${safe(dep.id)} ${safe(dep.version)}`).join(" · ")
          : "无依赖";
        return `<div class="release">
          <span class="version">v${safe(release.version)}</span>
          <span class="channel">${safe(release.channel)}</span>
          <span class="notes">${safe(release.releaseNotes)}<div class="deps">${deps}</div></span>
        </div>`;
      }).join("");
      return `<article class="asset">
        <div class="asset-head"><div><h3>${safe(item.id)}</h3><span class="owner">${safe(item.owner)}</span></div><span class="type">${safe(type)}</span></div>
        ${releases}
      </article>`;
    }).join("");
    empty.hidden = packages.length !== 0;
  }

  query.addEventListener("input", render);
  document.getElementById("refresh").addEventListener("click", () => location.reload());
  window.setInterval(() => location.reload(), 60000);
  render();
}());
