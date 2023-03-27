function validateInput(id) {
	var table = document.getElementById("choices");
	var active_row = table.rows[id];
	const priceInpRe = /[\.0-9]+/;
	if(active_row.className == "Choice"){
		var name = document.getElementById("inpName");
		var price = document.getElementById("inpPrice");
		var name_val = name.value;
		if(name_val.length < 3) {
			name.focus();
			return false;
		}
		if(!priceInpRe.test(price.value.trim())) {
			price.focus();
			return false;
		}
	}
	else if(active_row.className == "Header2") {
		name = document.getElementById("inpName").value;
	}
	return true;
}

function encodeHTML(s) {
    return s.replace(/&/g, '&amp;')
	        .replace(/</g, '&lt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#x27')
			.replace(/'/g, '&#x2F');
}

// С 22:00 25 марта до 03:00 26 марта
function freezeActiveRow(id) {
	if(id >= 0) {
		if(validateInput(id)) {
			var table = document.getElementById("choices");
			var active_row = table.rows[id];
			if(active_row.className == "Choice"){
				name = document.getElementById("inpName").value;
				price = document.getElementById("inpPrice").value;
				active_row.cells[1].innerHTML = encodeHTML(name);
				active_row.cells[2].innerHTML = encodeHTML(price);
			}
			else if(active_row.className == "Header2") {
				name = document.getElementById("inpName").value;
				//hdrLevel = document.getElementById("inpPrice").value;
				active_row.cells[1].innerHTML = "<b>"
				  + encodeHTML(name) + "</b>";
				active_row.cells[2].innerHTML = "";
			}
		}
		else {
			return false;
		}
	}
	return true;
}

function updateIDs() {
	var table = document.getElementById("choices");
	var rows = Array.from(table.rows);
	rows.forEach(function(row) {
		var links = row.cells[0].innerHTML;
		var idx = row.rowIndex;
		var newLinks = links.replace(/addRow\([0-9]*,/g, "addRow("
		+ idx + ",");
		row.cells[0].innerHTML = newLinks;
	});
}

function addRow(id, className) {
	var table = document.getElementById("choices");
	var active_row_holder = document.getElementById("active_row");
	var active_row_id = active_row_holder.innerText;
	console.log(active_row_id);
	if(!freezeActiveRow(active_row_id)) return false;
	var newRow = table.insertRow(id+1);
	var newId = newRow.rowIndex;
	active_row_holder.innerHTML = newId;
	newRow.className = className; // "Choice" or "Header2"
	var actionCell = newRow.insertCell(0);
	var nameCell = newRow.insertCell(1);
	var priceCell = newRow.insertCell(2);
	actionCell.innerHTML = "<a href='#' onclick='return addRow("
	+ newId + ", \"Choice\");'>task</a>" +
	" | <a href='#' onclick='return addRow("
	+ newId + ", \"Header2\");'>header</a>";
	nameCell.innerHTML = "<input id='inpName' type='text'/>";
	if(className == "Choice") {
		priceCell.innerHTML = "<input id='inpPrice' type='text'/>";
	}
	else {
		priceCell.innerHTML = "";
	}
	document.getElementById('inpName').focus();
	updateIDs();
	return false;
}

function saveChoices() {
	// [TBD]
}