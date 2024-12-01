document.addEventListener("DOMContentLoaded", function () {
    const currentDate = document.getElementById("current-date");
    const goalDateInput = document.getElementById("goal-date");
    const daysLeft = document.getElementById("days-left");

    // 현재 날짜 표시
    const today = new Date();
    currentDate.textContent = today.toLocaleDateString(); // 현재 날짜만 표시

    // 목표 날짜 설정
    goalDateInput.addEventListener("change", function () {
        const goalDate = new Date(goalDateInput.value);
        const timeDiff = goalDate.getTime() - today.getTime();
        const daysRemaining = Math.ceil(timeDiff / (1000 * 3600 * 24));
        daysLeft.textContent = `D-${daysRemaining}`;
    });

    // 파스텔톤 무지개 색상 배열
    const colors = ['pastel-red', 'pastel-orange', 'pastel-yellow', 'pastel-green', 'pastel-blue', 'pastel-purple'];

    // 타임 그리드 생성
    const timeGrid = document.getElementById("time-grid");
    for (let row = 0; row < 24; row++) { // 세로 24개
        for (let col = 0; col < 6; col++) { // 가로 6개
            const cell = document.createElement("div");
            cell.classList.add("time-cell");
            cell.addEventListener("click", function () {
                colors.forEach(color => cell.classList.remove(color)); // 기존 색상 제거
                if (cell.classList.toggle("active")) {
                    cell.classList.add(colors[row % colors.length]); // 클릭 시 색상 추가
                }
            });
            timeGrid.appendChild(cell);
        }
    }

    // 할 일 목록에서 Enter 키 입력 처리
    const taskTable = document.getElementById("task-table");
    taskTable.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            const activeElement = document.activeElement;
            if (activeElement && activeElement.tagName === "TD" && activeElement.hasAttribute("contenteditable")) {
                if (activeElement.dataset.placeholder === "할 일 입력") {
                    // 타이틀 셀에서 Enter 키를 누르면 서브타이틀 셀로 이동
                    const nextSibling = activeElement.nextElementSibling;
                    if (nextSibling && nextSibling.dataset.placeholder === "세부사항 입력") {
                        nextSibling.focus();
                    }
                } else if (activeElement.dataset.placeholder === "세부사항 입력") {
                    // 서브타이틀 셀에서 Enter 키를 누르면 새로운 행 추가
                    const newRow = taskTable.insertRow();
                    const newTitleCell = newRow.insertCell();
                    newTitleCell.setAttribute("contenteditable", "true");
                    newTitleCell.setAttribute("data-placeholder", "할 일 입력");
                    newTitleCell.classList.add("empty");

                    const newSubtitleCell = newRow.insertCell();
                    newSubtitleCell.setAttribute("contenteditable", "true");
                    newSubtitleCell.setAttribute("data-placeholder", "세부사항 입력");
                    newSubtitleCell.classList.add("empty");

                    // 새로운 셀에 포커스를 설정하여 사용자가 계속 입력할 수 있도록 함
                    newTitleCell.focus();
                }
            }
        }
    });

    // 입력이 지워졌을 때 플레이스홀더 표시
    taskTable.addEventListener("input", function (event) {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === "TD" && activeElement.hasAttribute("contenteditable")) {
            if (activeElement.textContent.trim() === "") {
                activeElement.classList.add("empty");
            } else {
                activeElement.classList.remove("empty");
            }
        }
    });

    // 초기화 및 페이지 로드 시 빈 셀에 대해 empty 클래스 추가
    const cells = taskTable.querySelectorAll("td[contenteditable='true']");
    cells.forEach(cell => {
        if (cell.textContent.trim() === "") {
            cell.classList.add("empty");
        }
    });
});
