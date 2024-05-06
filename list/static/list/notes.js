function sendNoteForm() {
    let note_form = document.getElementById("id-add-note-form");
    let url = note_form.action;
    let form_data = new FormData(note_form);

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
    })
    .catch(error => {
        // Handle errors
        console.error('There was a problem with the fetch operation:', error);
    });
}


window.addEventListener("load", (event) => {
    let note_form = document.getElementById("id-add-note-form");
    note_form.addEventListener("submit", event => {
        event.preventDefault();
        sendNoteForm();
    });
});
