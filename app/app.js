const tg = window.Telegram.WebApp;

tg.expand();
tg.ready();

const user = tg.initDataUnsafe?.user;

const app = document.getElementById("app");

if (user) {
    app.innerHTML = `
        <h2>Welcome, ${user.first_name}</h2>
        <p>User ID: ${user.id}</p>
        <button onclick="loadOrders()">Load Orders</button>
    `;
} else {
    app.innerHTML = "<h2>No Telegram user</h2>";
}

function loadOrders() {
    app.innerHTML += "<p>Orders will be here...</p>";
}