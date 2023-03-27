function setError(field, message) {
    const em = document.getElementById('error_msg_id');
    if(em) return;
    const br = document.createElement("br");
    const errorMsg = document.createElement("span");
    errorMsg.classList.add("error");
    errorMsg.textContent = message;
    br.id = 'br_id';
    errorMsg.id = 'error_msg_id';
    field.parentNode.appendChild(br);
    field.parentNode.appendChild(errorMsg);
    field.classList.add("invalid");
}

function unsetError(field) {
    if(!field.classList.contains('invalid')) return;
    field.classList.remove('invalid');
    const br = document.getElementById('br_id');
    const em = document.getElementById('error_msg_id');
    if(br) field.parentNode.removeChild(br);
    if(em) field.parentNode.removeChild(em);
}

function validateInput(id) {
	var table = document.getElementById("choices");
	var active_row = table.rows[id];
	const priceInpRe = /^\d+(\.\d+)?$/;
	if(active_row.className == "Choice"){
		var name  = document.getElementById("inpName");
		var price = document.getElementById("inpPrice");
		var name_val = name.value;
		if(name_val.length < 3) {
            setError(name, "3 or more symbols");
			name.focus();
			return false;
		}
        unsetError(name);
		if(!priceInpRe.test(price.value.trim())) {
            setError(price, "Define numeric price");
            price.focus();
			return false;
		}
        unsetError(price);
	}
	else if(active_row.className == "Header2") {
		var name = document.getElementById("inpName");
        var name_val = name.value;
        if(name_val.length < 3) {
            setError(name, "3 or more symbols");
            name.focus();
            return false;
        }
        unsetError(name);
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

function freezeActiveRow() {
	var active_row_holder = document.getElementById("active_row");
	var id = active_row_holder.innerText;
    console.log(id)
	if(id && id >= 0) {
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
				active_row.cells[1].innerHTML = "<b>"
				  + encodeHTML(name) + "</b>";
				active_row.cells[2].innerHTML = "";
			}
            active_row.cells[3].innerHTML = "<a href='#' onclick='return setDelete("
            + id + ");'>delete</a>";
		}
		else {
			return false;
		}
        active_row_holder.innerHTML = "-1";
	}
	return true;
}

function updateIDs() {
    const add_row_cell_idx = 0;
    const del_cell_idx = 3;
	var table = document.getElementById("choices");
	var rows = Array.from(table.rows);
	rows.forEach(function(row) {
		var links    = row.cells[add_row_cell_idx].innerHTML;
        var del_link = row.cells[del_cell_idx].innerHTML;
		var idx = row.rowIndex;
		var newLinks = links.replace(/addRow\([0-9]+,/g, "addRow("
		+ idx + ",");
        var new_del_link = del_link.replace(/setDelete\([0-9]+/,      "setDelete(" + idx)
                                   .replace(/restoreDeleted\([0-9]+/, "restoreDeleted(" + idx);
		row.cells[add_row_cell_idx].innerHTML = newLinks;
        row.cells[del_cell_idx].innerHTML = new_del_link;
	});
}

function restoreDeleted(id) {
    const name_cell_idx  = 1;
    const price_cell_idx = 2;
    const del_cell_idx   = 3;
    var table = document.getElementById("choices");
    var row = table.rows[id];
    row.cells[name_cell_idx].classList.remove('delete');
    row.cells[price_cell_idx].classList.remove('delete');
    var del_link = row.cells[del_cell_idx].innerHTML;
    var new_del_link = del_link.replace(/restoreDeleted/, "setDelete")
                               .replace(/restore/, "delete");
    row.cells[del_cell_idx].innerHTML = new_del_link;
    return false;
}

function setDelete(id) {
    const name_cell_idx  = 1;
    const price_cell_idx = 2;
    const del_cell_idx   = 3;
    var table = document.getElementById("choices");
    var row = table.rows[id];
    row.cells[name_cell_idx].classList.add('delete');
    row.cells[price_cell_idx].classList.add('delete');
    var del_link = row.cells[del_cell_idx].innerHTML;
    var new_del_link = del_link.replace(/setDelete/, "restoreDeleted")
                               .replace(/delete/, "restore");
    row.cells[del_cell_idx].innerHTML = new_del_link;
    return false;
}

function addRow(id, className) {
    const action_cell_idx = 0;
    const name_cell_idx   = 1;
    const price_cell_idx  = 2;
    const del_cell_idx    = 3;
	var table = document.getElementById("choices");
	var active_row_holder = document.getElementById("active_row");
	if(!freezeActiveRow()) return false;
	var newRow = table.insertRow(id+1);
	var newId = newRow.rowIndex;
	active_row_holder.innerHTML = newId;
	newRow.className = className; // "Choice" or "Header2"
	var actionCell = newRow.insertCell(action_cell_idx);
	var nameCell   = newRow.insertCell(name_cell_idx);
	var priceCell  = newRow.insertCell(price_cell_idx);
    var delCell    = newRow.insertCell(del_cell_idx);
	actionCell.innerHTML = "<a href='#' onclick='return addRow("
	+ newId + ", \"Choice\");'>task</a>" +
	" | <a href='#' onclick='return addRow("
	+ newId + ", \"Header2\");'>head</a>";
	nameCell.innerHTML = "<input id='inpName' type='text'/>";
	if(className == "Choice") {
		priceCell.innerHTML = "<input id='inpPrice' type='text'/>";
	} else {
		priceCell.innerHTML = "";
	}
    delCell.innerHTML = "";
	document.getElementById('inpName').focus();
	updateIDs();
	return false;
}

function saveChoices() {
	// [TBD]
}


function test1() {
    //debugger;
    addRow(0, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '100';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'walls';
    document.getElementById('inpPrice').value = 'kkk';
    addRow(2, "Choice");
    document.getElementById('inpPrice').value = '200';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'ceiling';
    document.getElementById('inpPrice').value = '300';
    addRow(0, "Header2");
    document.getElementById('inpName').value = 'house';
    addRow(0, "Header2");
    document.getElementById('inpName').value = 'garage';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'base';
    document.getElementById('inpPrice').value = '546';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '345';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'fl';
    document.getElementById('inpPrice').value = '89';
    setDelete(4);
    addRow(4, "Choice");
    document.getElementById('inpName').value = 'garage floor';
    addRow(4, "Choice");
    document.getElementById('inpName').value = 'roof';
    document.getElementById('inpPrice').value = '312';
    freezeActiveRow();
    addRow(0, "Header2");
    document.getElementById('inpName').value = 'ga';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'garden';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'grass';
    document.getElementById('inpPrice').value = '9ra';
    addRow(2, "Choice");
    document.getElementById('inpPrice').value = '974';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'aaa';
    document.getElementById('inpPrice').value = '000';
    freezeActiveRow();
    setDelete(3);
}
