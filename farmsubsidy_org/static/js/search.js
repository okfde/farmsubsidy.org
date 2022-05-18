import perspective from "https://cdn.jsdelivr.net/npm/@finos/perspective/dist/cdn/perspective.js";

const worker = perspective.worker();
const data = JSON.parse(document.getElementById('search-data').textContent);
const table = worker.table(data);

const elem = document.querySelector("perspective-viewer")
elem.load(table);

const defaultConfig = {
  aggregates: {"amount": "sum",},
  group_by: ["country", "year"],
  sort: [["amount", "desc"]],
  columns: ["amount"],
}


const toggleCheckbox = () => {
  const recipientIds = [...document.querySelectorAll('input[name="recipient_id"]:checked')].map(c => c.value)
  if (recipientIds.length > 0) {
    defaultConfig.filter = [["recipient_id", "in", recipientIds]]
  } else {
    defaultConfig.filter = []
  }
  elem.restore(defaultConfig)
}

const checkboxes = document.querySelectorAll('input[name="recipient_id"]')
checkboxes.forEach((checkbox) => {
  checkbox.addEventListener("change", toggleCheckbox)
})

elem.restore(defaultConfig)


