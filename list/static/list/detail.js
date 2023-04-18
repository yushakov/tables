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

const g_JsonNames = ['action', 'name', 'price', 'quantity', 'units',
                     'total_price', 'assigned_to', 'day_start', 'days',
                     'progress_bar', 'progress', 'delete_action'];

const g_header_del_col_span = 5;
const gLocale = "en-US";


window.onbeforeunload = function() {
    var modified_text = document.getElementById('modified').innerText;
    if(modified_text == 'yes') {
        return false;
    }
    return true;
}

function get_del_cell_text() {
    return "<a href='#' onclick='return setDelete(this);'"
        + "onmouseover='delMouseOver(this);' "
        + "onmouseout='delMouseOut(this);'>delete</a>"
        + "&nbsp;|&nbsp; <a href='#' onclick='return modifyRow(this);'"
        + "onmouseover='delMouseOver(this);'"
        + "onmouseout='delMouseOut(this);'>modify</a>";
}

function setForm() {
    //return;
    const form = document.getElementById('choices_form');
    form.addEventListener("submit", event => {
        event.preventDefault();
        saveChoices();
        form.submit();
    });
}

function showPrettyRaw(x) {
    var table = document.getElementById("choices");
    var rows = Array.from(table.rows);
    var btn   = document.getElementById("PrettyRawBtn");
    if(btn.innerText == "Show Pretty") {
        rows.forEach(function(row) {
           if(row.cells[g_name_cell_idx].classList.contains('delete')) {
               row.style.display = 'none';
           }
           row.cells[g_action_cell_idx].style.display = 'none';
           if(row.classList.contains('Choice')) {
               row.cells[g_del_cell_idx].style.display    = 'none';
           } else {
               var header_del = row.cells[g_del_cell_idx-g_header_del_col_span+1];
               header_del.style.display = 'none';
           }
        });
        btn.innerText = "Show Raw";
    } else {
        rows.forEach(function(row) {
           if(row.cells[g_name_cell_idx].classList.contains('delete')) {
               row.style.display = 'table-row';
           }
           row.cells[g_action_cell_idx].style.display = 'block';
           if(row.classList.contains('Choice')) {
               row.cells[g_del_cell_idx].style.display    = 'block';
           } else {
               var header_del = row.cells[g_del_cell_idx-g_header_del_col_span+1];
               header_del.style.display = 'block';
           }
        });
        btn.innerText = "Show Pretty";
    }
}

function delMouseOver(x) {
    x.parentNode.parentNode.classList.add("onDelMouseOver");
}

function delMouseOut(x) {
    x.parentNode.parentNode.classList.remove("onDelMouseOver");
}

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

function badNumber(element, message, min=null, max=null) {
	const numberInpRe = /^\d+(,\d+)*(\.\d+)?$/;
    if(!numberInpRe.test(element.value.trim()) ||
       (min != null && element.value.trim() < min) ||
       (max != null && element.value.trim() > max)) {
        setError(element, message);
        element.focus();
        return true;
    }
    unsetError(element);
    return false;
}

function validateInput(id) {
	var table = document.getElementById("choices");
	var active_row = table.rows[id];
	const numberInpRe = /^\d+(\.\d+)?$/;
	if(active_row.className == "Choice"){
		var name     = document.getElementById("inpName");
		var price    = document.getElementById("inpPrice");
        var qty      = document.getElementById("inpQty");
        var units    = document.getElementById("inpUnits");
        var asgnTo   = document.getElementById("inpAsgnTo");
        var dayStart = document.getElementById("inpDayStart");
        var planDays = document.getElementById("inpPlanDays");
        var progress = document.getElementById("inpProgress");
		var name_val = name.value;
		if(name_val.length < 3) {
            setError(name, "3 or more symbols");
			name.focus();
			return false;
		}
        if(badNumber(price,    "Input a number.")) return false;
        if(badNumber(qty,      "Input a number.")) return false;
        if(badNumber(planDays, "Input a number.")) return false;
        if(badNumber(progress, "Number between 0 and 100.", 0, 100)) return false;
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

function modify(ths) {
    document.getElementById('modified').innerText = 'yes';
    console.log(ths.innerText);
    //var text = ths.innerText;
    //ths.innerHTML = "<input type='text' value='" + text + "'/>";
}

function modifyRow(ths) {
	if(!freezeActiveRow()) return false;
    var elem = document.getElementById('modified');
    if(elem) elem.innerText = 'yes';
    if(!ths || !ths.parentNode) return false;
    var active_row = ths.parentNode.parentNode;
    if(!active_row) return false;

    del_cell_idx  = g_del_cell_idx;
    active_row.classList.remove("onDelMouseOver");
    if(!active_row.classList.contains("Choice")) {
        del_cell_idx -= g_header_del_col_span-1;
    }
    var del_cell_html = active_row.cells[del_cell_idx].innerText;
    del_cell_html = del_cell_html.replace('modify', '')
                                 .replace('delete', '')
                                 .replace('|', '');
    active_row.cells[del_cell_idx].innerText = del_cell_html;

    var name     = active_row.cells[g_name_cell_idx     ].innerText;
    var price    = active_row.cells[g_price_cell_idx    ].innerText.replace('£', '').trim();
    var qty      = active_row.cells[g_qty_cell_idx      ].innerText;
    var units    = active_row.cells[g_units_cell_idx    ].innerText;
    var asgnTo   = active_row.cells[g_asgn_to_cell_idx  ].innerText;
    var dayStart = active_row.cells[g_day_start_cell_idx].innerText;
    active_row.cells[g_name_cell_idx     ].innerHTML
	    = "<textarea id='inpName' rows='5' cols='40'>" + name + "</textarea>";
    if(active_row.classList.contains("Choice")) {
        var planDays = active_row.cells[g_plan_days_cell_idx].innerText;
        var progress = active_row.cells[g_prog_pcnt_cell_idx].innerText.replace('%','').trim();
        active_row.cells[g_price_cell_idx    ].innerHTML
            = "<input id='inpPrice' type='text' size='5'    value='" + price + "'/>";
        active_row.cells[g_qty_cell_idx      ].innerHTML
            = "<input id='inpQty' type='text' size='3'      value='" + qty + "'/>";
        active_row.cells[g_units_cell_idx    ].innerHTML
            = "<input id='inpUnits' type='text' size='3'    value='" + units + "'/>";
        active_row.cells[g_asgn_to_cell_idx  ].innerHTML
            = "<input id='inpAsgnTo' type='text' size='5'   value='" + asgnTo + "'/>";
        active_row.cells[g_day_start_cell_idx].innerHTML
            = "<input id='inpDayStart' type='text' size='5' value='" + dayStart + "'/>";
        active_row.cells[g_plan_days_cell_idx].innerHTML
            = "<input id='inpPlanDays' type='text' size='2' value='" + planDays + "'/>";
        active_row.cells[g_progress_cell_idx ].innerHTML
            = "<input id='inpProgress' type='text' size='2' value='" + progress + "'/>";  
    }
    var acro = document.getElementById("active_row");
    if(acro) acro.innerHTML = active_row.rowIndex;
    else console.log("ERROR: can't get 'active_row'");
    return false;
}

function freezeActiveRow() {
	var active_row_holder = document.getElementById("active_row");
	var id = active_row_holder.innerText;
    let del_cell_idx = g_del_cell_idx;
	if(id && id >= 0) {
		if(validateInput(id)) {
			var table = document.getElementById("choices");
			var active_row = table.rows[id];
			if(active_row.classList.contains("Choice")){
				var name     = document.getElementById("inpName").value;
				var price    = document.getElementById("inpPrice").value;
                var price_num = Number(price.replace(/,/g,''));
				var qty      = document.getElementById("inpQty").value;
				var units    = document.getElementById("inpUnits").value;
				var asgnTo   = document.getElementById("inpAsgnTo").value;
				var dayStart = document.getElementById("inpDayStart").value;
				var planDays = document.getElementById("inpPlanDays").value;
				var progress = document.getElementById("inpProgress").value;
				active_row.cells[g_name_cell_idx].innerHTML = encodeHTML(name);
				active_row.cells[g_price_cell_idx].innerHTML = '&#163; ' + price_num.toLocaleString(gLocale);
				active_row.cells[g_price_cell_idx].style.textAlign = 'right';
				active_row.cells[g_qty_cell_idx ].innerHTML = encodeHTML(qty);
				active_row.cells[g_qty_cell_idx ].style.textAlign = 'right';
				active_row.cells[g_units_cell_idx].innerHTML = encodeHTML(units);
				active_row.cells[g_tot_prc_cell_idx].innerHTML
                                           = '&#163; ' + Number(price_num * Number(qty)).toLocaleString(gLocale);
				active_row.cells[g_tot_prc_cell_idx].style.textAlign = 'right';
				active_row.cells[g_asgn_to_cell_idx].innerHTML = encodeHTML(asgnTo);
				active_row.cells[g_day_start_cell_idx].innerHTML = encodeHTML(dayStart);
				active_row.cells[g_plan_days_cell_idx].innerHTML = encodeHTML(planDays);
				active_row.cells[g_plan_days_cell_idx].style.textAlign = 'center';
                active_row.cells[g_progress_cell_idx].innerHTML = 
                        "<td><progress max='100' value='" + progress + "'></progress></td>";
                active_row.cells[g_prog_pcnt_cell_idx].innerHTML = 
                        "<td align='right'>" + progress + " %</td>";
			}
			else if(active_row.classList.contains("Header2")) {
                del_cell_idx -= g_header_del_col_span-1;
				name = document.getElementById("inpName").value;
				active_row.cells[g_name_cell_idx].innerHTML = ""
				  + encodeHTML(name) + "";
                active_row.cells[g_name_cell_idx].classList.add("td_header_2");
                active_row.cells[g_name_cell_idx].colSpan = g_header_del_col_span;
				active_row.cells[g_price_cell_idx].innerHTML = "";
                active_row.cells[del_cell_idx].classList.add("td_header_2");
			}
            active_row.cells[del_cell_idx].classList.add("del_modif_cell");
            active_row.cells[del_cell_idx].innerHTML = get_del_cell_text();
            while(active_row.cells.length-1 > del_cell_idx) {
                active_row.deleteCell(active_row.cells.length-1);
            }
		}
		else {
			return false;
		}
        active_row_holder.innerHTML = "-1";
        updateHeaders();
	}
	return true;
}

function updateIDs() {
    var table = document.getElementById("choices");
    var rows = Array.from(table.rows);
    var active_row_id = document.getElementById("active_row").innerHTML;
    rows.forEach(function(row) {
        try {
            var idx = row.rowIndex;
            if(idx > active_row_id) {
                var links    = row.cells[g_action_cell_idx].innerHTML;
                var newLinks = links.replace(/addRow\([0-9]+,/g, "addRow(" + idx + ",");
                row.cells[g_action_cell_idx].innerHTML = newLinks;
            }
        }
        catch(exception){
            console.log('Caught: ' + exception);
            console.log('>> row index: ' + row.rowIndex);
            console.log('>> row.cells[0]: ' + row.cells[0].innerHTML);
        }
	});
}

function setHeaderTotal(header, price) {
    var inner = header.cells[g_name_cell_idx].innerHTML;
    header_name = inner.split('£')[0].replace(/&nbsp;/g, '').trim();
    header.cells[g_name_cell_idx].innerHTML
        = header_name + '&nbsp;&nbsp;&nbsp;&#163;'
        + Number(price).toLocaleString(gLocale) + ' (total)';
}

function updateHeaders() {
    var active_row = document.getElementById("active_row").innerText;
    if(Number(active_row) > 0) return;
    var table = document.getElementById("choices");
    var rows = Array.from(table.rows);
    var last_header = null;
    var price = 0.0;
    var total_price = 0.0;
    rows.forEach(function(row) {
        if(row.rowIndex > 0) {
            if(row.classList.contains("Header2")
               && !row.cells[g_name_cell_idx].classList.contains("delete")) {
                if(last_header) {
                    setHeaderTotal(last_header, price);
                }
                total_price += price;
                last_header  = row;
                price        = 0.0;
            } else {
                var cell = row.cells[g_tot_prc_cell_idx];
                var text = cell.innerText;
                if(!cell.classList.contains('delete')
                   && text.length > 0
                   && text.search(/£/) >= 0) {
                    try {
                        var row_price = text.split('£')[1].trim();
                        price += Number(row_price.replace(/,/g, ''));
                    }
                    catch(exception) {
                        console.log(exception);
                    }
                }
                if(row.rowIndex == rows.length-1) {
                    total_price += price;
                    if(last_header) {
                        setHeaderTotal(last_header, price);
                    }
                }
            }
        }
    });
    var project_total     = document.getElementById("project_total");
    var project_total_vat = document.getElementById("project_total_vat");
    var project_vat       = document.getElementById("project_vat").innerHTML;
    var vat = Number(project_vat.replace(/%/,'').trim());
    project_total.innerHTML = '&#163; ' + total_price.toLocaleString(gLocale);
    project_total_vat.innerHTML
        = '&#163; ' + Number(Math.round(total_price * (1.0 + 0.01 * vat))).toLocaleString(gLocale);
}

function restoreDeleted(ths) {
    var row = ths.parentNode.parentNode;
    row.cells[g_name_cell_idx].classList.remove('delete');
    row.cells[g_price_cell_idx].classList.remove('delete');
    row.cells[g_qty_cell_idx].classList.remove('delete');
    row.cells[g_units_cell_idx].classList.remove('delete');
    row.cells[g_tot_prc_cell_idx].classList.remove('delete');
    row.cells[g_asgn_to_cell_idx].classList.remove('delete');
    row.cells[g_day_start_cell_idx].classList.remove('delete');
    if(row.classList.contains('Choice')) {
        row.cells[g_plan_days_cell_idx].classList.remove('delete');
        row.cells[g_prog_pcnt_cell_idx].classList.remove('delete');
    }
    var del_link = ths.parentNode.innerHTML;
    var new_del_link = del_link.replace(/restoreDeleted/, "setDelete")
                               .replace(/restore/, "delete");
    ths.parentNode.innerHTML = new_del_link;
    updateHeaders();
    return false;
}

function setDelete(ths) {
    var row = ths.parentNode.parentNode;
    row.cells[g_name_cell_idx].classList.add('delete');
    row.cells[g_price_cell_idx].classList.add('delete');
    row.cells[g_qty_cell_idx].classList.add('delete');
    row.cells[g_units_cell_idx].classList.add('delete');
    row.cells[g_tot_prc_cell_idx].classList.add('delete');
    row.cells[g_asgn_to_cell_idx].classList.add('delete');
    row.cells[g_day_start_cell_idx].classList.add('delete');
    if(row.classList.contains('Choice')) {
        row.cells[g_plan_days_cell_idx].classList.add('delete');
        row.cells[g_prog_pcnt_cell_idx].classList.add('delete');
    }
    var del_link = ths.parentNode.innerHTML;
    var new_del_link = del_link.replace(/setDelete/, "restoreDeleted")
                               .replace(/delete/, "restore");
    ths.parentNode.innerHTML = new_del_link;
    updateHeaders();
    document.getElementById('modified').innerText = 'yes';
    return false;
}

function getToday() {
    const date = new Date();
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function addRow(id, className) {
	var table = document.getElementById("choices");
	var active_row_holder = document.getElementById("active_row");
    document.getElementById('modified').innerText = 'yes';
	if(!freezeActiveRow()) return false;
	var newRow;
    if(id < table.rows.length) {
        newRow = table.insertRow(id+1);
    } else {
        console.log("ERROR: row index is too big to be added!")
        return false;
    }
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
    newRow.insertCell(g_del_cell_idx);
	actionCell.innerHTML = "<a href='#' onclick='return addRow("
	                     + newId + ", \"Choice\");'>task</a>"
	                     + " | <a href='#' onclick='return addRow("
	                     + newId + ", \"Header2\");'>head</a>";
	nameCell.innerHTML = "<textarea id='inpName' rows='5' cols='40'></textarea>";
	if(className == "Choice") {
		priceCell.innerHTML    = "<input id='inpPrice' type='text' size='5'/>";
        qtyCell.innerHTML      = "<input id='inpQty' type='text' size='3' value='1'/>";
        unitsCell.innerHTML    = "<input id='inpUnits' type='text' size='3' value='nr'/>";
        asgnToCell.innerHTML   = "<input id='inpAsgnTo' type='text' size='5' value='Somebody'/>";
        dayStartCell.innerHTML = "<input id='inpDayStart' type='text' size='5' value='" + getToday() + "'/>";
        planDaysCell.innerHTML = "<input id='inpPlanDays' type='text' size='2' value='1'/>";
        progressCell.innerHTML = "<input id='inpProgress' type='text' size='2' value='0.0'/>";
	} else {
		priceCell.innerHTML = "";
	}
	document.getElementById('inpName').focus();
	updateIDs();
	return false;
}

function saveChoices() {
	if(!freezeActiveRow()) return false;
    var modified_cell = document.getElementById('modified')
    if(modified_cell.innerText == 'no') return false;
    var table = document.getElementById('choices')
    var rows = Array.from(table.rows);
    var out = {};
    rows.forEach(function(row) {
        if(row.rowIndex == 0) return;
        var cells = Array.from(row.cells);
        var cell_dict = {};
        cells.forEach(function(cell) {
            if(cell.cellIndex == 0) return;
            if(cell.cellIndex == 1) cell_dict["class"] = String(cell.className);
            cell_dict[g_JsonNames[cell.cellIndex]] = String(cell.innerText);
        });
        out["row_" + String(row.rowIndex)] =
           {"id": String(row.id), "class": String(row.classList), "cells": cell_dict};
    });
    modified.innerText = 'no';
    document.getElementById('json_input').value = JSON.stringify(out);
    return true;
}

function setDeleteByRowIdx(idx) {
    var row = document.getElementById("choices").rows[idx];
    var cells = Array.from(row.cells);
    cells.forEach(function(cell) {
        if(cell.classList.contains("del_modif_cell")) {
            cell.childNodes[0].onclick();
        }
    });
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
    document.getElementById('inpPrice').value = '1,000,500';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '345';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'fl';
    document.getElementById('inpPrice').value = '89';
    setDeleteByRowIdx(4);
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
    setDeleteByRowIdx(3);
}

function test2() {
    //debugger;
    var table = document.getElementById("choices")
    addRow(table.rows.length-1, "Choice")
    document.getElementById("inpName").value = 'chimney';
    document.getElementById("inpPrice").value = 'price';
    document.getElementById("inpQty").value = 'three';
    document.getElementById("inpPlanDays").value = '7 (seven)';
    freezeActiveRow()
    document.getElementById("inpPrice").value = '150';
    document.getElementById("inpQty").value = '3';
    document.getElementById("inpPlanDays").value = '7';
    freezeActiveRow() 
    addRow(0, "Choice");
    document.getElementById("inpName").value = 'chimney better here';
    document.getElementById("inpPrice").value = '153';
    document.getElementById("inpQty").value = '3';
    document.getElementById("inpPlanDays").value = '5';
    setDeleteByRowIdx(table.rows.length-1);
    freezeActiveRow();
    setDeleteByRowIdx(table.rows.length-1);
    setDeleteByRowIdx(table.rows.length-1);
}

function addHouse() {
    //debugger;
    addRow(0, "Header2");
    document.getElementById('inpName').value = 'House';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'base';
    document.getElementById('inpPrice').value = '10,000';
    document.getElementById('inpPlanDays').value = '10';
    document.getElementById('inpAsgnTo').value = 'Vasya';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '1000';
    document.getElementById('inpPlanDays').value = '5';
    document.getElementById('inpAsgnTo').value = 'Vasya';
    addRow(3, "Choice");
    document.getElementById('inpName').value = 'walls';
    document.getElementById('inpPrice').value = '750';
    document.getElementById('inpQty').value = '4';
    document.getElementById('inpPlanDays').value = '12';
    document.getElementById('inpAsgnTo').value = 'Kolya';
    addRow(4, "Choice");
    document.getElementById('inpName').value = 'ceiling';
    document.getElementById('inpPrice').value = '1300';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '7';
    document.getElementById('inpAsgnTo').value = 'Andrew';
    addRow(5, "Choice");
    document.getElementById('inpName').value = 'roof';
    document.getElementById('inpPrice').value = '3,000';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '14';
    document.getElementById('inpAsgnTo').value = 'Robert';
    freezeActiveRow();
}

function addGarage() {
    //debugger;
    addRow(0, "Header2");
    document.getElementById('inpName').value = 'Garage';
    addRow(1, "Choice");
    document.getElementById('inpName').value = 'base';
    document.getElementById('inpPrice').value = '5,000';
    document.getElementById('inpPlanDays').value = '10';
    document.getElementById('inpAsgnTo').value = 'Illarion';
    addRow(2, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '300';
    document.getElementById('inpPlanDays').value = '5';
    document.getElementById('inpAsgnTo').value = 'Ivan';
    addRow(3, "Choice");
    document.getElementById('inpName').value = 'tools';
    document.getElementById('inpPrice').value = '2,500';
    document.getElementById('inpQty').value = '3';
    document.getElementById('inpPlanDays').value = '11';
    document.getElementById('inpAsgnTo').value = 'Nikolay Stankov';
    addRow(4, "Choice");
    document.getElementById('inpName').value = 'walls';
    document.getElementById('inpPrice').value = '250';
    document.getElementById('inpQty').value = '4';
    document.getElementById('inpPlanDays').value = '2';
    document.getElementById('inpAsgnTo').value = 'Kolya';
    addRow(5, "Choice");
    document.getElementById('inpName').value = 'ceiling';
    document.getElementById('inpPrice').value = '500';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '3';
    document.getElementById('inpAsgnTo').value = 'Andrew';
    addRow(6, "Choice");
    document.getElementById('inpName').value = 'roof';
    document.getElementById('inpPrice').value = '500';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '7';
    document.getElementById('inpAsgnTo').value = 'David';
    freezeActiveRow();
}

function addGarageBottomUp() {
    //debugger;
    var rows = document.getElementById("choices").rows;
    var lastIdx = rows.length - 1;
    addRow(lastIdx, "Header2");
    document.getElementById('inpName').value = 'Garage';
    addRow(lastIdx+1, "Choice");
    document.getElementById('inpName').value = 'base';
    document.getElementById('inpPrice').value = '5,000';
    document.getElementById('inpPlanDays').value = '10';
    document.getElementById('inpAsgnTo').value = 'Illarion';
    addRow(lastIdx+2, "Choice");
    document.getElementById('inpName').value = 'floor';
    document.getElementById('inpPrice').value = '300';
    document.getElementById('inpPlanDays').value = '5';
    document.getElementById('inpAsgnTo').value = 'Ivan';
    addRow(lastIdx+3, "Choice");
    document.getElementById('inpName').value = 'tools';
    document.getElementById('inpPrice').value = '2,500';
    document.getElementById('inpQty').value = '3';
    document.getElementById('inpPlanDays').value = '11';
    document.getElementById('inpAsgnTo').value = 'Nikolay Stankov';
    addRow(lastIdx+4, "Choice");
    document.getElementById('inpName').value = 'walls';
    document.getElementById('inpPrice').value = '250';
    document.getElementById('inpQty').value = '4';
    document.getElementById('inpPlanDays').value = '2';
    document.getElementById('inpAsgnTo').value = 'Kolya';
    addRow(lastIdx+5, "Choice");
    document.getElementById('inpName').value = 'ceiling';
    document.getElementById('inpPrice').value = '500';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '3';
    document.getElementById('inpAsgnTo').value = 'Andrew';
    addRow(lastIdx+6, "Choice");
    document.getElementById('inpName').value = 'roof';
    document.getElementById('inpPrice').value = '500';
    document.getElementById('inpQty').value = '1';
    document.getElementById('inpPlanDays').value = '7';
    document.getElementById('inpAsgnTo').value = 'David';
    freezeActiveRow();
}
