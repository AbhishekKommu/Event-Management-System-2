async function loadUser() {

    const response = await fetch("/api/user");

    const data = await response.json();

    if (!data.logged_in) {
        window.location.href = "/login";
        return;
    }

    document.getElementById("username").textContent =
        data.user.name;
}


async function loadDashboard() {

    const response = await fetch("/api/events");

    const data = await response.json();

    if (!data.success) {
        return;
    }

    const events = data.events;

    document.getElementById("totalEvents").textContent =
        events.length;

    const today = new Date()
        .toISOString()
        .split("T")[0];

    const upcoming = events.filter(event =>
        event.date >= today
    );

    document.getElementById("upcomingEvents").textContent =
        upcoming.length;
}


async function logout() {

    await fetch("/api/logout", {
        method: "POST"
    });

    window.location.href = "/login";
}


document
    .getElementById("logoutBtn")
    .addEventListener("click", logout);


loadUser();
loadDashboard();
