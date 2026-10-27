/* Espace administrateur : statistiques, CRUD et réservations via l'API. */
const errorEl = document.getElementById("admin-error");

function showError(message) {
  errorEl.textContent = message || "";
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Erreur ${res.status}`);
  }
  return body;
}

function money(value) {
  return Number(value).toFixed(2).replace(".", ",") + " €";
}

async function loadStats() {
  const stats = await api("/api/admin/stats");
  document.getElementById("stat-boxes").innerHTML = [
    ["Réservations confirmées", stats.total_reservations],
    ["Places vendues", stats.total_seats],
    ["Revenus", money(stats.total_revenue)],
    ["Remplissage global", stats.global_fill_rate + " %"],
  ].map(([label, value]) => `<div class="stat-box"><strong>${value}</strong>${label}</div>`).join("");
  document.getElementById("stats-films").innerHTML = stats.per_film.map((f) =>
    `<tr><td>${f.title}</td><td>${f.reservations}</td><td>${f.seats}</td><td>${money(f.revenue)}</td><td>${f.fill_rate} %</td></tr>`).join("");
  document.getElementById("stats-rooms").innerHTML = stats.per_room.map((r) =>
    `<tr><td>${r.name}</td><td>${r.seats}</td><td>${r.fill_rate} %</td></tr>`).join("");
  document.getElementById("stats-screenings").innerHTML = stats.per_screening.map((s) =>
    `<tr><td>${s.film_title}</td><td>${s.room_name}</td><td>${new Date(s.start_time).toLocaleString("fr-FR")}</td><td>${s.reserved} / ${s.capacity}</td><td>${s.fill_rate} %</td><td>${money(s.revenue)}</td></tr>`).join("");
}

async function loadFilms() {
  const films = await api("/api/admin/films");
  document.getElementById("films-list").innerHTML = films.map((f) =>
    `<tr><td>${f.title}</td><td>${f.genre}</td><td>${f.duration_min} min</td><td>${f.release_year}</td>` +
    `<td><button class="btn btn-small btn-danger" onclick="deleteItem('/api/admin/films/${f.id}', loadFilms)">Supprimer</button></td></tr>`).join("");
  document.getElementById("screening-film").innerHTML = films.map((f) =>
    `<option value="${f.id}">${f.title}</option>`).join("");
}

async function loadRooms() {
  const rooms = await api("/api/admin/rooms");
  document.getElementById("rooms-list").innerHTML = rooms.map((r) =>
    `<tr><td>${r.name}</td><td>${r.room_type}</td><td>${r.capacity}</td><td>${r.rows} x ${r.cols}</td>` +
    `<td><button class="btn btn-small btn-danger" onclick="deleteItem('/api/admin/rooms/${r.id}', loadRooms)">Supprimer</button></td></tr>`).join("");
  document.getElementById("screening-room").innerHTML = rooms.map((r) =>
    `<option value="${r.id}">${r.name}</option>`).join("");
}

async function loadScreenings() {
  const screenings = await api("/api/admin/screenings");
  document.getElementById("screenings-list").innerHTML = screenings.map((s) =>
    `<tr><td>${s.film_title}</td><td>${s.room_name}</td><td>${new Date(s.start_time).toLocaleString("fr-FR")}</td><td>${money(s.price)}</td>` +
    `<td><button class="btn btn-small btn-danger" onclick="deleteItem('/api/admin/screenings/${s.id}', loadScreenings)">Supprimer</button></td></tr>`).join("");
}

async function loadBookings() {
  const bookings = await api("/api/admin/bookings");
  document.getElementById("bookings-list").innerHTML = bookings.map((b) =>
    `<tr><td>${b.user_email}</td><td>${b.film_title}</td><td>${b.room_name}</td><td>${new Date(b.start_time).toLocaleString("fr-FR")}</td>` +
    `<td>${b.seats.join(", ")}</td><td>${money(b.total)}</td><td>${b.status}</td>` +
    `<td>${b.status === "confirmed" ? `<button class="btn btn-small btn-danger" onclick="cancelBooking(${b.id})">Annuler</button>` : ""}</td></tr>`).join("");
}

async function deleteItem(path, reload) {
  if (!confirm("Confirmer la suppression ?")) return;
  try {
    await api(path, {method: "DELETE"});
    showError("");
    await reload();
  } catch (error) {
    showError(error.message);
  }
}

async function cancelBooking(id) {
  try {
    await api(`/api/admin/bookings/${id}/cancel`, {method: "POST"});
    showError("");
    await loadBookings();
  } catch (error) {
    showError(error.message);
  }
}

function bindForm(formId, path, reload) {
  document.getElementById(formId).addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target).entries());
    for (const key of ["duration_min", "release_year", "rows", "cols", "film_id", "room_id"]) {
      if (data[key] !== undefined && data[key] !== "") data[key] = Number(data[key]);
    }
    if (data.price !== undefined && data.price !== "") data.price = Number(data.price);
    if (data.rows !== undefined && data.cols !== undefined) {
      data.capacity = data.rows * data.cols;
    }
    try {
      await api(path, {method: "POST", body: JSON.stringify(data)});
      showError("");
      event.target.reset();
      await reload();
    } catch (error) {
      showError(error.message);
    }
  });
}

const loaders = {
  stats: loadStats,
  films: loadFilms,
  rooms: loadRooms,
  screenings: async () => { await loadFilms(); await loadRooms(); await loadScreenings(); },
  bookings: loadBookings,
};

document.querySelectorAll(".admin-tabs button").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".admin-tabs button").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    document.querySelectorAll("[id^='tab-']").forEach((tab) => { tab.hidden = true; });
    const tab = button.dataset.tab;
    document.getElementById("tab-" + tab).hidden = false;
    try {
      await loaders[tab]();
      showError("");
    } catch (error) {
      showError(error.message);
    }
  });
});

bindForm("film-form", "/api/admin/films", loadFilms);
bindForm("room-form", "/api/admin/rooms", loadRooms);
bindForm("screening-form", "/api/admin/screenings", loadScreenings);
loadStats().catch((error) => showError(error.message));
