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
        // Before dropping, show a dialog near cursor:
        //  "Do you want put Construct to Status in Category?"
        // yes/no
        //   And and the optional text field for a Note.
        ev.target.appendChild(document.getElementById(construct_id));
    }
}