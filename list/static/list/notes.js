function sendNoteForm() {
    let note_form = document.getElementById("id-add-note-form");
    let url = note_form.action;
    let form_data = new FormData(note_form);
    let input_text = document.getElementById('id-note-text').value;

    if (input_text.trim().length == 0) return;

    fetch(url, {
        method: 'POST',
        body: form_data,
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
        console.log(data);
        let note_list = document.getElementById("id-note-list");
        let notes = note_list.getElementsByClassName("note");
        let new_note = document.createElement('div');
        new_note.classList.add('note');
        new_note.id = 'note-' + data['note_id'];
        let note_head = document.createElement('div');
        note_head.classList.add('note-head');
        note_head.innerHTML = "<b>" + data['last_modified'] + "</b> by "
                            + "<a href='#'>" + data['author'] + "</a>";
        new_note.appendChild(note_head);
        let note_text = document.createElement('div');
        note_text.classList.add('note-text');
        note_text.innerHTML = note_markup(data['text']);
        new_note.appendChild(note_text);
        if (notes.length > 0) {
            notes[0].parentNode.insertBefore(new_note, notes[0]);
        }
        else {
            note_list.appendChild(new_note);
        }
        document.getElementById('id-note-text').value = '';
    })
    .catch(error => {
        // Handle errors
        console.error('There was a problem with the fetch operation:', error);
    });
}


function note_markup(str) {
    let out = str.trim();
    out = str.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    out = out.replace(/\*(.*?)\*/g, "<i>$1</i>")
    out = out.replace(/\n/g, "<br />")
    out = out.replace(/"&amp;/g, "&")
    out = out.replace(/\[([^\]]+)\]\(([^\s\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    return out;
}


window.addEventListener("load", (event) => {
    let note_form = document.getElementById("id-add-note-form");
    note_form.addEventListener("submit", event => {
        event.preventDefault();
        sendNoteForm();
    });
});