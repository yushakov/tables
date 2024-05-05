function open_tab(tab_content_id, ths) {
    var i;
    var x = document.getElementsByClassName("tab-content");
    for (i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
    document.getElementById(tab_content_id).style.display = "block";
    var x = document.getElementsByClassName("tab");
    for (i = 0; i < x.length; i++) {
        x[i].className = "tab";
    }
    ths.className = "tab active-tab";
}
