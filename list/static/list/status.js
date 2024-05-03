function openChain(chainName, ths) {
    var i;
    var x = document.getElementsByClassName("chain");
    for (i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
    document.getElementById(chainName).style.display = "block";
    var x = document.getElementsByClassName("tab");
    for (i = 0; i < x.length; i++) {
        x[i].className = "tab";
    }
    ths.className = "tab active-tab";
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
    ev.dataTransfer.setData("status_id_from", ev.target.parentNode.id);
    var parent = ev.target.parentNode;
    while (!parent.classList.contains("chain")) {
        parent = parent.parentNode;
    }
    var chain_id = parent.id;
    ev.dataTransfer.setData("chain_id_from", chain_id);
}

function drop(ev) {
    ev.preventDefault();
    var construct_id = ev.dataTransfer.getData("text");
    if (ev.target.classList.contains("status-col")) {
        var parent = ev.target.parentNode;
        while (!parent.classList.contains("chain")) {
            parent = parent.parentNode;
        }
        var chain_id = parent.id;
        var status_id = ev.target.id;
        console.log(construct_id);
        console.log("From: " + ev.dataTransfer.getData("chain_id_from")
                    + ", " + ev.dataTransfer.getData("status_id_from"));
        console.log("To: " + chain_id + ", " + status_id);
        let parameters = {construct_id: construct_id,
            chain_from: ev.dataTransfer.getData("chain_id_from"),
            status_from: ev.dataTransfer.getData("status_id_from"),
            chain_to: chain_id,
            status_to: status_id
        }
        ev.target.appendChild(document.getElementById(construct_id));
        showDropDialog(parameters);
    }
}

function showDropDialog(par) {
    var dialog = document.getElementById("id_drop_dialog");
    var content = document.getElementById("id_dialog_content");
    dialog.style.display = "block";
    var centerX = window.innerWidth / 2.0;
    var centerY = window.innerHeight / 2.0 + window.scrollY;
    dialog.style.paddingTop = (centerY - content.offsetHeight / 2) + 'px';
    dialog.style.paddingLeft = (centerX - content.offsetWidth / 2) + 'px';
    document.getElementById("id_construct_name").innerText = window.names[par.construct_id];
    document.getElementById("id_source").innerText = window.names[par.chain_from]
                                                   + ", " + window.names[par.status_from];
    document.getElementById("id_destination").innerText = window.names[par.chain_to]
                                                        + ", " + window.names[par.status_to] + "  ?";
    window.dialog_parameters = par;
}

function highlightElement(element) {
    element.classList.add('highlight');
    element.addEventListener('animationend', () => {
        element.classList.remove('highlight');
    }, { once: true });
}

function dialogYes() {
    // TODO:
    // 1. Send new data to the server in background
    var dialog = document.getElementById("id_drop_dialog");
    dialog.style.display = "none";
    var construct_badge = document.getElementById(window.dialog_parameters.construct_id);
    highlightElement(construct_badge);
    window.dialog_parameters = {};
}

function dialogNo() {
    var dialog = document.getElementById("id_drop_dialog");
    var construct_badge = document.getElementById(window.dialog_parameters.construct_id);
    dialog.style.display = "none";
    document.getElementById(window.dialog_parameters.status_from)
            .appendChild(construct_badge);
    var tab_id = window.dialog_parameters.chain_from.replace(/chain-/, "tab-");
    var tab = document.getElementById(tab_id);
    openChain(window.dialog_parameters.chain_from, tab);
    window.dialog_parameters = {};
    highlightElement(construct_badge);
}

function constructTouch(ths) {
    var field = document.getElementById("id_chosen_construct");
    field.innerText = ths.innerText;
}