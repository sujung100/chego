// 달력 시작

window.onload = function () { buildCalendar(); }    // 웹 페이지가 로드되면 buildCalendar 실행

let nowMonth = new Date();  // 현재 달을 페이지를 로드한 날의 달로 초기화
let today = new Date();     // 페이지를 로드한 날짜를 저장
today.setHours(0, 0, 0, 0);    // 비교 편의를 위해 today의 시간을 초기화

// 달력 생성 : 해당 달에 맞춰 테이블을 만들고, 날짜를 채워 넣는다.
function buildCalendar() {

    let firstDate = new Date(nowMonth.getFullYear(), nowMonth.getMonth(), 1);     // 이번달 1일
    let lastDate = new Date(nowMonth.getFullYear(), nowMonth.getMonth() + 1, 0);  // 이번달 마지막날

    let tbody_Calendar = document.querySelector(".Calendar > tbody");
    document.getElementById("calYear").innerText = nowMonth.getFullYear();             // 연도 숫자 갱신
    document.getElementById("calMonth").innerText = leftPad(nowMonth.getMonth() + 1);  // 월 숫자 갱신

    while (tbody_Calendar.rows.length > 0) {                        // 이전 출력결과가 남아있는 경우 초기화
        tbody_Calendar.deleteRow(tbody_Calendar.rows.length - 1);
    }

    let nowRow = tbody_Calendar.insertRow();        // 첫번째 행 추가           

    for (let j = 0; j < firstDate.getDay(); j++) {  // 이번달 1일의 요일만큼
        let nowColumn = nowRow.insertCell();        // 열 추가
    }

    for (let nowDay = firstDate; nowDay <= lastDate; nowDay.setDate(nowDay.getDate() + 1)) {   // day는 날짜를 저장하는 변수, 이번달 마지막날까지 증가시키며 반복  

        let nowColumn = nowRow.insertCell();        // 새 열을 추가하고


        let newDIV = document.createElement("p");
        newDIV.innerHTML = leftPad(nowDay.getDate());        // 추가한 열에 날짜 입력
        nowColumn.appendChild(newDIV);

        if (nowDay.getDay() == 6) {                 // 토요일인 경우
            nowRow = tbody_Calendar.insertRow();    // 새로운 행 추가
        }

        if (nowDay < today) {                       // 지난날인 경우
            newDIV.className = "pastDay";
        }
        else if (nowDay.getFullYear() == today.getFullYear() && nowDay.getMonth() == today.getMonth() && nowDay.getDate() == today.getDate()) { // 오늘인 경우           
            newDIV.className = "today";
            newDIV.onclick = function () { choiceDate(this); }
        }
        else {                                      // 미래인 경우
            newDIV.className = "futureDay";
            newDIV.onclick = function () { choiceDate(this); }
        }
    }
}

// 날짜 선택
function choiceDate(newDIV) {
    if (document.getElementsByClassName("choiceDay")[0]) {                              // 기존에 선택한 날짜가 있으면
        document.getElementsByClassName("choiceDay")[0].classList.remove("choiceDay");  // 해당 날짜의 "choiceDay" class 제거
    }
    newDIV.classList.add("choiceDay");           // 선택된 날짜에 "choiceDay" class 추가

     // 선택한 날짜 가져오기
     const selectedYear = nowMonth.getFullYear();
     const selectedMonth = nowMonth.getMonth() + 1; // getMonth()는 0부터 시작하므로 +1
     const selectedDate = newDIV.innerHTML;

     // 폼에 선택한 날짜 입력하기
     document.getElementById("selectedYearInput").value = selectedYear;
     document.getElementById("selectedMonthInput").value = selectedMonth;
     document.getElementById("selectedDateInput").value = selectedDate;
 
     // 폼 서버로 제출하기
     document.getElementById("dateForm").submit();
}

// 이전달 버튼 클릭
function prevCalendar() {
    nowMonth = new Date(nowMonth.getFullYear(), nowMonth.getMonth() - 1, nowMonth.getDate());   // 현재 달을 1 감소
    buildCalendar();    // 달력 다시 생성
}
// 다음달 버튼 클릭
function nextCalendar() {
    nowMonth = new Date(nowMonth.getFullYear(), nowMonth.getMonth() + 1, nowMonth.getDate());   // 현재 달을 1 증가
    buildCalendar();    // 달력 다시 생성
}

// input값이 한자리 숫자인 경우 앞에 '0' 붙혀주는 함수
function leftPad(value) {
    if (value < 10) {
        value = "0" + value;
        return value;
    }
    return value;
}


// function updateButtons() {
//     var selectedDate = $("#user_selected_date").val(); // 사용자가 선택한 날짜를 얻어옵니다.

//     $(".time-item").each(function() { // 각 작성되었던 버튼들을 순차적으로 접근하여 처리
//     var timeDate = $(this).data("date"); // 버튼의 data-date 값 즉, Time 테이블의 select_date

//     if (timeDate === selectedDate) { // 사용자가 선택한 날짜와 Time 테이블의 select_date 값이 같다면
//         $(this).show(); // 버튼 보여주기
//     } else {
//         $(this).hide(); // 달라지면 버튼 숨기기
//     }
//     });
// }

// // 달력 끝

// // 날짜 선택 이벤트 발생 시 input 필드에 선택한 날짜 값을 설정
// $("#calendar").on("date_selected", function(event, date) {
//     $("#user_selected_date").val(date);
//     updateButtons(); // 새로 작성한 함수 호출
// });



//   // 달력에서 날짜 클릭하면 값 전달
//   const timeItems = document.querySelectorAll('.time-item');

// // Add the click event listener for each 'time-item' element
//   timeItems.forEach(item => {
//     item.addEventListener('click', function() {
//       // Get the time value from the 'data-time' attribute
//       const selectedTime = this.getAttribute('data-time');
      
//       // Set the value of the 'input type="time"' element with the selected time value
//       document.getElementById('user_time').value = selectedTime;
//     });
//   });




// 달력 title에 상호명 띄우고 클릭한 업체 배경색 변경
// 시간선택 -> 다음 버튼 나타나게
document.addEventListener('DOMContentLoaded', function () {
    let timeItems = document.querySelectorAll('.time-item');
    let nextButton = document.getElementById('next-button');

    document.querySelectorAll('.store-table').forEach(function (storeTable) {
    storeTable.addEventListener('click', function () {
        const storeName = storeTable.querySelector('.st-name');
        document.getElementById('selected-store').innerText = storeName.innerText;

        document.querySelectorAll('.store-table').forEach(function (others) {
        if (others !== storeTable) {
            others.classList.remove('selected');

            // otherItem 확인 및 제거
            others.querySelectorAll('.time-item').forEach(function (otherItem) {
            otherItem.classList.remove('green');
            });
        }
        });

        storeTable.classList.add('selected');
        updateNextButton();
    });
    });

    function updateNextButton() {
    let hasGreen = Array.from(timeItems).some(
        (item) => item.classList.contains('green')
    );

    if (hasGreen) {
        nextButton.style.display = 'block';
    } else {
        nextButton.style.display = 'none';
    }
    }

    timeItems.forEach(function (item) {
    item.addEventListener('click', function () {
        timeItems.forEach(function (otherItem) {
        if (otherItem.closest('.store-table.selected') !== null) {
            if (otherItem !== item) {
            otherItem.classList.remove('green');
            }
        }
        });

        item.classList.toggle('green');
        updateNextButton();
    });
    });

    updateNextButton();
});






// 날짜 선택안하면 alert 띄우기
function checkSelectedDate() {
    const selectedDate = document.getElementsByClassName("choiceDay");
    if (selectedDate.length === 0) {
        alert("날짜를 선택해주세요.");
    } else {
        // 사용자가 선택한 날짜에 대한 처리를 여기에서 수행하세요.
    }
}