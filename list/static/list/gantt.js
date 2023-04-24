const tasks = [
    { name: "Task 1", info: "Info 1", start: 0, end: 3 },
    { name: "Task 2", info: "Info 2", start: 2, end: 7 },
    { name: "Task 3", info: "Info 3", start: 5, end: 9 },
];

const N = 10;

window.addEventListener("load", getGlobals);
//window.addEventListener("resize", createChart);

function getGlobals() {
}

function createGanttRow(task) {
    const row = document.createElement("tr");
    const taskName = document.createElement("td");
    const taskInfo = document.createElement("td");
    const ganttContainer = document.createElement("td");
    ganttContainer.style.width = `calc(70%)`;
    ganttContainer.style.position = 'relative';
    ganttContainer.colSpan = N;

    taskName.textContent = task.name;
    taskInfo.textContent = task.info;

    const ganttBar = document.createElement("div");
    ganttBar.classList.add("gantt-bar");
    ganttBar.style.left = `calc(${(task.start / N) * 100}% + 1px)`;
    ganttBar.style.width = `calc(${((task.end - task.start + 1) / N) * 100}% - 1px)`;
    ganttBar.textContent = task.name;

    ganttContainer.appendChild(ganttBar);

    row.appendChild(taskName);
    row.appendChild(taskInfo);
    row.appendChild(ganttContainer);

    return row;
}

const ganttHeader = document.getElementById("gantt-header");
for (let i = 1; i <= N; i++) {
    const dl = document.createElement("th");
    dl.innerHTML = `<b>day ${i}</b>`;
    dl.style.width = `calc(70% / ${N})`;
    ganttHeader.appendChild(dl);
}

const ganttChart = document.getElementById("gantt-chart");
tasks.forEach(task => {
    ganttChart.appendChild(createGanttRow(task));
});

