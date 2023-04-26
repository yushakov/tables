let gAllDays = -1;

function getGlobals() {
    var total_days = document.getElementById("total_days");
    gAllDays = Number(total_days.innerText);
    //makeExpandableCells();
    formChart();
}

function createGanttRow(row, task) {
    const ganttContainer = document.createElement("td");
    ganttContainer.classList.add("gantt-container");
    ganttContainer.style.width = `calc(${gAllDays * 31}px)`;
    ganttContainer.colSpan = gAllDays;
    const ganttBar = document.createElement("div");
    ganttBar.classList.add("gantt-bar");
    ganttBar.style.left = `calc(${task.start * 31}px + 1px)`;
    ganttBar.style.width = `calc(${(task.end - task.start + 1) * 31}px - 1px)`;
    ganttBar.textContent = task.name;
    ganttContainer.appendChild(ganttBar);
    row.appendChild(ganttContainer);
}

function formChart() {
    const start_day_cell = document.getElementById("common_start");
    start_day_cell.colSpan = gAllDays;
    const ganttHeader = document.getElementById("gantt-header");
    var labels = document.getElementById("day_labels").innerText;
    labels = labels.split(',');
    for (let i = 0; i < gAllDays; i++) {
        const dl = document.createElement("th");
        dl.innerHTML = `<b>${labels[i]}</b>`;
        dl.style.width = `30px`;
        dl.classList.add("day_cell");
        ganttHeader.appendChild(dl);
    }
    const ganttChart = document.getElementById("gantt-chart");
    const rows = Array.from(ganttChart.rows);
    var task_list = document.getElementById("task_list");
    tasks = JSON.parse(task_list.innerText.replace(/&quot;/g, '"'));
    rows.forEach(function(row) {
        if(row.rowIndex == 0) return;
        var task_id = Number(row.id.replace(/tr_/, ''));
        createGanttRow(row, tasks[task_id]);
    });
}

function makeExpandableCells() {
    const expandableCells = document.querySelectorAll(".task_name");
    expandableCells.forEach((cell) => {
        cell.addEventListener("mouseover", () => {
            cell.style.maxHeight = "none";
            console.log("mouseover");
        });
        cell.addEventListener("mouseout", () => {
            cell.style.maxHeight = "1.2em";
        });
    });
}

window.addEventListener("load", getGlobals);
//window.addEventListener("resize", createChart);
