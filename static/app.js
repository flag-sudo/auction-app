const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;
let username = user ? (user.username || user.first_name) : "guest";


async function createLot(){

    const data = {
        title: document.getElementById("title").value,
        desc: document.getElementById("desc").value,
        price: document.getElementById("price").value,
        blitz: document.getElementById("blitz").value,
        step: document.getElementById("step").value,
        time: document.getElementById("time").value,
        seller: username
    };

    await fetch("/create_lot", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify(data)
    });

    location.reload();
}


async function bid(id){

    await fetch(`/bid/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user: username})
    });

    location.reload();
}


async function customBid(id){

    let v = prompt("Цена:");

    await fetch(`/custom_bid/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user: username, value:Number(v)})
    });

    location.reload();
}


async function blitz(id){

    await fetch(`/blitz/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user: username})
    });

    location.reload();
}
