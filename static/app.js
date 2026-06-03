const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;
let username = user ? (user.username || user.first_name) : "guest";

async function createLot(){

    await fetch("/create_lot", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
            title:title.value,
            desc:desc.value,
            price:price.value,
            blitz:blitz.value,
            step:step.value,
            time:time.value,
            seller:username
        })
    });

    location.reload();
}

async function bid(id){
    await fetch(`/bid/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user:username})
    });
    location.reload();
}

async function customBid(id){

    let v = prompt("price");

    await fetch(`/custom_bid/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user:username, value:Number(v)})
    });

    location.reload();
}

async function blitz(id){

    await fetch(`/blitz/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user:username})
    });

    location.reload();
}

async function unlock(id){

    const r = await fetch(`/unlock/${id}`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({user:username})
    });

    const d = await r.json();

    if(d.ok){
        alert("seller: " + d.seller);
    }
}
