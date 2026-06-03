const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;
let username = user ? (user.username || user.first_name) : "guest";


async function bid(id, step){

    await fetch(`/bid/${id}`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({user: username})
    });

    location.reload();
}


async function blitz(id){

    await fetch(`/blitz/${id}`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({user: username})
    });

    location.reload();
}
