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
    localStorage.setItem('active-tab', ths.id);
    localStorage.setItem('active-tab-content', tab_content_id);
}

window.addEventListener("load", (event) => {
    let active_tab_id = localStorage.getItem('active-tab');
    let active_tab_content_id = localStorage.getItem('active-tab-content');
    if (active_tab_id) {
        let tab = document.getElementById(active_tab_id);
        open_tab(active_tab_content_id, tab);
    }
});
