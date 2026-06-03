const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;
let username = user ? (user.username || user.first_name) : "guest";

async function bid(lotId, button){

    const res = await fetch(`/bid/${lotId}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({user: username})
    });

    const data = await res.json();

    if(data.ok){
        const lot = button.closest(".lot");

        lot.querySelector(".info").innerHTML +=
            `<div>👑 Лидер: <b>${data.leader}</b></div>`;
    }
}
