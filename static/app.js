const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;

let username = "guest";

if (user) {
    username = user.username || user.first_name;
}

async function bid(lotId, button){

    const res = await fetch(`/bid/${lotId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user: username
        })
    });

    const data = await res.json();

    if(data.ok){

        const lot = button.closest(".lot");

        lot.querySelector(".price").innerHTML =
            "💰 Ставка: <b>" + data.price + " грн</b>";

        alert("👑 Лидер: " + data.leader);
    }
}