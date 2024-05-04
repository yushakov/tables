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
    if (ev.target.classList.contains("status-col") ||
        ev.target.classList.contains("status-col-head") ||
        ev.target.classList.contains("construct")) {
        var parent = ev.target.parentNode;
        while (!parent.classList.contains("chain")) {
            parent = parent.parentNode;
        }
        var node = ev.target;
        while (!node.classList.contains("status-col")) {
            node = node.parentNode;
        }
        var chain_id = parent.id;
        var status_id = node.id;
        let parameters = {construct_id: construct_id,
            chain_from: ev.dataTransfer.getData("chain_id_from"),
            status_from: ev.dataTransfer.getData("status_id_from"),
            chain_to: chain_id,
            status_to: status_id
        }
        var previous_construct = null;
        var col_head = node.getElementsByClassName("status-col-head")[0];
        if (ev.target.classList.contains("construct")) {
            previous_construct = ev.target;
        }
        let construct_badge = document.getElementById(construct_id);
        if (previous_construct && previous_construct.nextSibling) {
            node.insertBefore(construct_badge, previous_construct.nextSibling);
        }
        else if (col_head.nextSibling) {
            node.insertBefore(construct_badge, col_head.nextSibling);
        }
        else {
            node.appendChild(construct_badge);
        }
        showDropDialog(parameters);
    }
}

function showDropDialog(par) {
    var dialog = document.getElementById("id_drop_dialog");
    var content = document.getElementById("id_dialog_content");
    dialog.style.display = "block";
    var centerX = window.innerWidth / 2.0;
    var centerY = window.innerHeight / 2.0;
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

function showWaitImage() {
    var dialog_content = document.getElementById("id_dialog_content");
    dialog_content.style.display = "none";
    var wait_img = document.getElementById("id_wait_img");
    wait_img.style.display = "block";
}

function hideWaitImage() {
    var dialog_content = document.getElementById("id_dialog_content");
    dialog_content.style.display = "block";
    var wait_img = document.getElementById("id_wait_img");
    wait_img.style.display = "none";
}

function dialogYes() {
    let note = document.getElementById("id_moving_note").value;
    window.dialog_parameters.note = note;
    showWaitImage();
    sendData();
}

function cleanDialog() {
    window.dialog_parameters = {};
    document.getElementById("id_construct_name").value = "";
    document.getElementById("id_source").value = "";
    document.getElementById("id_destination").value = "";
    document.getElementById("id_moving_note").value = "";
}

function dataSent() {
    hideWaitImage();
    var dialog = document.getElementById("id_drop_dialog");
    dialog.style.display = "none";
    var construct_badge = document.getElementById(window.dialog_parameters.construct_id);
    highlightElement(construct_badge);
    cleanDialog();
}

function sendData() {
    document.getElementById('dialog-data').value = JSON.stringify(window.dialog_parameters);
    var formData = new FormData(document.getElementById("id-fetch-form"));
    fetch(window.fetch_url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest', // This header helps server-side to identify the request as AJAX
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Handle success. You can update the UI accordingly.
        console.log(data); // Assuming the server responds with some JSON
        dataSent();
    })
    .catch(error => {
        // Handle errors
        console.error('There was a problem with the fetch operation:', error);
    });
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
    cleanDialog();
    construct_badge.focus();
    highlightElement(construct_badge);
}

function constructTouch(ths) {
    var field = document.getElementById("id_chosen_construct");
    field.innerText = ths.innerText;
}