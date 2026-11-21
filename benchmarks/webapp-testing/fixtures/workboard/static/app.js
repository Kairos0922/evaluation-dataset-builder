const state = {
  items: [],
  summary: { all: 0, open: 0, in_progress: 0, done: 0 },
  deleteId: null,
};

const rows = document.getElementById("task-rows");
const statusMessage = document.getElementById("status-message");
const emptyState = document.getElementById("empty-state");
const searchInput = document.getElementById("task-search");
const statusFilter = document.getElementById("status-filter");
const deleteDialog = document.getElementById("delete-dialog");

function showMessage(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.dataset.state = isError ? "error" : "success";
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || `Request failed: ${response.status}`);
  }
  return body;
}

function renderSummary(summary) {
  document.getElementById("count-all").textContent = summary.all;
  document.getElementById("count-open").textContent = summary.open;
  document.getElementById("count-in-progress").textContent = summary.in_progress;
  document.getElementById("count-done").textContent = summary.done;
}

function statusLabel(status) {
  return {
    open: "Open",
    in_progress: "In progress",
    done: "Done",
  }[status] || status;
}

function nextStatus(status) {
  return {
    open: "in_progress",
    in_progress: "done",
    done: "open",
  }[status] || "open";
}

function renderRows(items) {
  rows.replaceChildren();
  emptyState.hidden = items.length !== 0;

  for (const item of items) {
    const row = document.createElement("tr");
    const taskCell = document.createElement("td");
    const title = document.createElement("strong");
    const description = document.createElement("small");
    title.textContent = item.title;
    description.textContent = item.description;
    taskCell.append(title, description);

    const priorityCell = document.createElement("td");
    priorityCell.textContent = item.priority;

    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `status-pill status-${item.status}`;
    status.textContent = statusLabel(item.status);
    statusCell.append(status);

    const actionCell = document.createElement("td");
    actionCell.className = "action-cell";
    const changeButton = document.createElement("button");
    changeButton.type = "button";
    changeButton.className = "text-button change-status";
    changeButton.dataset.id = item.id;
    changeButton.textContent = `Move to ${statusLabel(nextStatus(item.status))}`;
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "text-button delete-task";
    deleteButton.dataset.id = item.id;
    deleteButton.textContent = "Delete";
    actionCell.append(changeButton, deleteButton);

    row.append(taskCell, priorityCell, statusCell, actionCell);
    rows.append(row);
  }
}

async function loadTasks() {
  try {
    const params = new URLSearchParams({
      q: searchInput.value,
      status: statusFilter.value,
    });
    const result = await request(`/api/tasks?${params.toString()}`);
    state.items = result.items;
    state.summary = result.summary;
    renderSummary(result.summary);
    renderRows(result.items);
  } catch (error) {
    showMessage(error.message, true);
  }
}

searchInput.addEventListener("input", loadTasks);
statusFilter.addEventListener("change", loadTasks);

document.getElementById("create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = {
    title: form.elements.title.value,
    description: form.elements.description.value,
    priority: form.elements.priority.value,
  };
  try {
    const result = await request("/api/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });
    form.reset();
    showMessage(`Created ${result.item.id}`);
    await loadTasks();
  } catch (error) {
    showMessage(error.message, true);
  }
});

rows.addEventListener("click", async (event) => {
  const changeButton = event.target.closest(".change-status");
  const deleteButton = event.target.closest(".delete-task");

  if (changeButton) {
    const item = state.items.find((task) => task.id === changeButton.dataset.id);
    if (!item) return;
    try {
      await request(`/api/tasks/${encodeURIComponent(item.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus(item.status) }),
      });
      showMessage(`Updated ${item.id}`);
      await loadTasks();
    } catch (error) {
      showMessage(error.message, true);
    }
  }

  if (deleteButton) {
    state.deleteId = deleteButton.dataset.id;
    deleteDialog.showModal();
  }
});

document.getElementById("confirm-delete").addEventListener("click", async () => {
  if (!state.deleteId) return;
  const id = state.deleteId;
  try {
    await request(`/api/tasks/${encodeURIComponent(id)}`, { method: "DELETE" });
    deleteDialog.close();
    state.deleteId = null;
    showMessage(`Deleted ${id}`);
    await loadTasks();
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.getElementById("cancel-delete").addEventListener("click", () => {
  state.deleteId = null;
});

deleteDialog.addEventListener("close", () => {
  state.deleteId = null;
});

loadTasks();
