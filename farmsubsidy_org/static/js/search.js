import perspective from "https://cdn.jsdelivr.net/npm/@finos/perspective/dist/cdn/perspective.js";

const worker = perspective.worker();
const data = JSON.parse(document.getElementById('search-data').textContent);
const table = worker.table(data);
document.querySelector("perspective-viewer").load(table);
