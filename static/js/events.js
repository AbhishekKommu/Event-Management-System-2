const eventsContainer =
    document.getElementById("eventsContainer");

const eventForm =
    document.getElementById("eventForm");

const formSection =
    document.getElementById("eventFormSection");

const showFormBtn =
    document.getElementById("showFormBtn");

let allEvents = [];


// -------------------------
// Show Form
// -------------------------

showFormBtn.addEventListener("click", () => {

    formSection.classList.toggle("hidden");

});


// -------------------------
// Load Events
// -------------------------

async function loadEvents() {

    const response = await fetch("/api/events");

    const data = await response.json();

    if (!data.success) {
        return;
    }

    allEvents = data.events;

    displayEvents(allEvents);
}


// -------------------------
// Display Events
// -------------------------

function displayEvents(events) {

    eventsContainer.innerHTML = "";

    if (events.length === 0) {

        eventsContainer.innerHTML =
            "<p>No events found.</p>";

        return;
    }


    events.forEach(event => {

        const card = document.createElement("div");

        card.className = "event-card";

        card.innerHTML = `

            <h2>${event.title}</h2>

            <p>
                ${event.description || ""}
            </p>

            <p>
                <strong>Date:</strong>
                ${event.date}
            </p>

            <p>
                <strong>Time:</strong>
                ${event.time}
            </p>

            <p>
                <strong>Location:</strong>
                ${event.location}
            </p>

            <p>
                <strong>Category:</strong>
                ${event.category}
            </p>

            <p>
                <strong>Organizer:</strong>
                ${event.organizer}
            </p>

            <button onclick="editEvent(${event.id})">
                Edit
            </button>

            <button
                class="danger"
                onclick="deleteEvent(${event.id})">
                Delete
            </button>
        `;

        eventsContainer.appendChild(card);

    });
}


// -------------------------
// Create Event
// -------------------------

eventForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const eventData = {

        title:
            document.getElementById("title").value,

        description:
            document.getElementById("description").value,

        date:
            document.getElementById("date").value,

        time:
            document.getElementById("time").value,

        location:
            document.getElementById("location").value,

        category:
            document.getElementById("category").value
    };


    const response = await fetch("/api/events", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(eventData)

    });


    const data = await response.json();

    alert(data.message);

    if (data.success) {

        eventForm.reset();

        formSection.classList.add("hidden");

        loadEvents();
    }

});


// -------------------------
// Edit Event
// -------------------------

async function editEvent(id) {

    const event = allEvents.find(
        event => event.id === id
    );

    if (!event) {
        return;
    }


    const title =
        prompt("Event title:", event.title);

    if (title === null) {
        return;
    }


    const description =
        prompt(
            "Description:",
            event.description || ""
        );


    const location =
        prompt(
            "Location:",
            event.location
        );


    const response = await fetch(
        `/api/events/${id}`,
        {
            method: "PUT",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                title: title,

                description: description,

                date: event.date,

                time: event.time,

                location: location,

                category: event.category

            })
        }
    );


    const data = await response.json();

    alert(data.message);

    loadEvents();
}


// -------------------------
// Delete Event
// -------------------------

async function deleteEvent(id) {

    const confirmation =
        confirm(
            "Are you sure you want to delete this event?"
        );

    if (!confirmation) {
        return;
    }


    const response = await fetch(
        `/api/events/${id}`,
        {
            method: "DELETE"
        }
    );


    const data = await response.json();

    alert(data.message);

    loadEvents();
}


// -------------------------
// Search
// -------------------------

document
    .getElementById("searchInput")
    .addEventListener("input", function() {

        const search =
            this.value.toLowerCase();

        const filtered =
            allEvents.filter(event =>

                event.title
                    .toLowerCase()
                    .includes(search)

                ||

                event.category
                    .toLowerCase()
                    .includes(search)

                ||

                event.location
                    .toLowerCase()
                    .includes(search)
            );

        displayEvents(filtered);

    });


// -------------------------
// Logout
// -------------------------

document
    .getElementById("logoutBtn")
    .addEventListener("click", async () => {

        await fetch("/api/logout", {
            method: "POST"
        });

        window.location.href = "/login";

    });


loadEvents();
