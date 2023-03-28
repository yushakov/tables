const g_action_cell_idx    = 0;
const g_name_cell_idx      = 1;
const g_price_cell_idx     = 2;
const g_qty_cell_idx       = 3;
const g_units_cell_idx     = 4;
const g_tot_prc_cell_idx   = 5;
const g_asgn_to_cell_idx   = 6;
const g_day_start_cell_idx = 7;
const g_plan_days_cell_idx = 8;
const g_progress_cell_idx  = 9;
const g_prog_pcnt_cell_idx = 10;
const g_del_cell_idx       = 11;

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
				name     = document.getElementById("inpName").value;
				price    = document.getElementById("inpPrice").value;
				qty      = document.getElementById("inpQty").value;
				units    = document.getElementById("inpUnits").value;
				asgnTo   = document.getElementById("inpAsgnTo").value;
				dayStart = document.getElementById("inpDayStart").value;
				planDays = document.getElementById("inpPlanDays").value;
				active_row.cells[g_name_cell_idx].innerHTML = encodeHTML(name);
				active_row.cells[g_price_cell_idx].innerHTML = '&#163; ' + encodeHTML(price);
				active_row.cells[g_qty_cell_idx ].innerHTML = encodeHTML(qty);
				active_row.cells[g_units_cell_idx].innerHTML = encodeHTML(units);
				active_row.cells[g_tot_prc_cell_idx].innerHTML
                                           = '&#163; ' + String(Number(price) * Number(qty));
				active_row.cells[g_asgn_to_cell_idx].innerHTML = encodeHTML(asgnTo);
				active_row.cells[g_day_start_cell_idx].innerHTML = encodeHTML(dayStart);
				active_row.cells[g_plan_days_cell_idx].innerHTML = encodeHTML(planDays);
			}
			else if(active_row.className == "Header2") {
				name = document.getElementById("inpName").value;
				active_row.cells[g_name_cell_idx].innerHTML = ""
				  + encodeHTML(name) + "";
                active_row.cells[g_name_cell_idx].classList.add("td_header_2");
                active_row.cells[g_name_cell_idx].colSpan = 5;
				active_row.cells[g_price_cell_idx].innerHTML = "";
                active_row.cells[g_del_cell_idx].classList.add("td_header_2");
			}
            active_row.cells[g_del_cell_idx].innerHTML = "<a href='#' onclick='return setDelete("
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
	var table = document.getElementById("choices");
	var rows = Array.from(table.rows);
	rows.forEach(function(row) {
        try {
            var links    = row.cells[g_action_cell_idx].innerHTML;
            var del_link = row.cells[g_del_cell_idx].innerHTML;
            var idx = row.rowIndex;
            var newLinks = links.replace(/addRow\([0-9]+,/g, "addRow("
            + idx + ",");
            var new_del_link = del_link.replace(/setDelete\([0-9]+/,      "setDelete(" + idx)
                                       .replace(/restoreDeleted\([0-9]+/, "restoreDeleted(" + idx);
            row.cells[g_action_cell_idx].innerHTML = newLinks;
            row.cells[g_del_cell_idx].innerHTML = new_del_link;
            console.log('g_del_cell_idx: ' + g_del_cell_idx);
        }
        catch(exception){
            console.log('Caught: ' + exception);
            console.log('>> row index: ' + row.rowIndex);
            console.log('>> row.cells[0]: ' + row.cells[0].innerHTML);
        }
	});
}

function restoreDeleted(id) {
    var table = document.getElementById("choices");
    var row = table.rows[id];
    row.cells[g_name_cell_idx].classList.remove('delete');
    row.cells[g_price_cell_idx].classList.remove('delete');
    row.cells[g_qty_cell_idx].classList.remove('delete');
    row.cells[g_units_cell_idx].classList.remove('delete');
    row.cells[g_tot_prc_cell_idx].classList.remove('delete');
    row.cells[g_asgn_to_cell_idx].classList.remove('delete');
    row.cells[g_day_start_cell_idx].classList.remove('delete');
    row.cells[g_plan_days_cell_idx].classList.remove('delete');
    var del_link = row.cells[g_del_cell_idx].innerHTML;
    var new_del_link = del_link.replace(/restoreDeleted/, "setDelete")
                               .replace(/restore/, "delete");
    row.cells[g_del_cell_idx].innerHTML = new_del_link;
    return false;
}

function setDelete(id) {
    var table = document.getElementById("choices");
    var row = table.rows[id];
    row.cells[g_name_cell_idx].classList.add('delete');
    row.cells[g_price_cell_idx].classList.add('delete');
    row.cells[g_qty_cell_idx].classList.add('delete');
    row.cells[g_units_cell_idx].classList.add('delete');
    row.cells[g_tot_prc_cell_idx].classList.add('delete');
    row.cells[g_asgn_to_cell_idx].classList.add('delete');
    row.cells[g_day_start_cell_idx].classList.add('delete');
    row.cells[g_plan_days_cell_idx].classList.add('delete');
    var del_link = row.cells[g_del_cell_idx].innerHTML;
    var new_del_link = del_link.replace(/setDelete/, "restoreDeleted")
                               .replace(/delete/, "restore");
    row.cells[g_del_cell_idx].innerHTML = new_del_link;
    return false;
}

function addRow(id, className) {
	var table = document.getElementById("choices");
	var active_row_holder = document.getElementById("active_row");
	if(!freezeActiveRow()) return false;
	var newRow = table.insertRow(id+1);
	var newId = newRow.rowIndex;
	active_row_holder.innerHTML = newId;
	newRow.className = className; // "Choice" or "Header2"
	var actionCell   = newRow.insertCell(g_action_cell_idx);
	var nameCell     = newRow.insertCell(g_name_cell_idx);
	var priceCell    = newRow.insertCell(g_price_cell_idx);
	var qtyCell      = newRow.insertCell(g_qty_cell_idx);
	var unitsCell    = newRow.insertCell(g_units_cell_idx);
	var totPriceCell = newRow.insertCell(g_tot_prc_cell_idx);
	var asgnToCell   = newRow.insertCell(g_asgn_to_cell_idx);
	var dayStartCell = newRow.insertCell(g_day_start_cell_idx);
	var planDaysCell = newRow.insertCell(g_plan_days_cell_idx);
	var progressCell = newRow.insertCell(g_progress_cell_idx);
	var progPcntCell = newRow.insertCell(g_prog_pcnt_cell_idx);
    var delCell      = newRow.insertCell(g_del_cell_idx);
	actionCell.innerHTML = "<a href='#' onclick='return addRow("
	+ newId + ", \"Choice\");'>task</a>" +
	" | <a href='#' onclick='return addRow("
	+ newId + ", \"Header2\");'>head</a>";
	nameCell.innerHTML = "<input id='inpName' type='text'/>";
	if(className == "Choice") {
		priceCell.innerHTML    = "<input id='inpPrice' type='text' size='5'/>";
        qtyCell.innerHTML      = "<input id='inpQty' type='text' size='3' value='1'/>";
        unitsCell.innerHTML    = "<input id='inpUnits' type='text' size='3' value='nr'/>";
        asgnToCell.innerHTML   = "<input id='inpAsgnTo' type='text' size='5' value='Somebody'/>";
        dayStartCell.innerHTML = "<input id='inpDayStart' type='text' size='5' value='Today'/>";
        planDaysCell.innerHTML = "<input id='inpPlanDays' type='text' size='2' value='1'/>";
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

