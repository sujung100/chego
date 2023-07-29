
//<![CDATA[

window.campReservation = 'Y';

var commn = {};
commn.nvl = function(a, b){

function isNull(value){
var _chkStr = value + '';
if(_chkStr == '' || _chkStr == null || _chkStr == 'null' ){
return true;
}
return false;
}

function isUndefined(value){
if(typeof(value) == undefined || typeof(value) == 'undefined' || value == 'undefined' || value == undefined){return true;}
return false;
}

if(isNull(b) || isUndefined(b)){
b = '';
}

if(isNull(a) || isUndefined(a)){
return b;
}else{
return a;
}
};

commn.callAjax = function(props){

var settings = {};
props.isShowLoading = props.isShowLoading || 'Y';
settings.dataType = 'json';
settings.method = 'post';
settings.url = props.url;
settings.data = props.data;

if(props.headers){
settings.headers = props.headers;
}
if(props.isShowLoading == 'Y'){
settings.beforeSend = showLoading;
settings.complete = maskBackgroundOff;
}
if(props.method){
settings.method = props.method;
}
if(props.dataType){
settings.dataType = props.dataType;
}

return $.ajax(settings);
};

commn.getDayWeekNm = function(dayWeek){
switch (dayWeek) {
case 1: 
case '1': return "월";
case 2: 
case '2': return "화";
case 3:
case '3': return "수";
case 4: 
case '4': return "목";
case 5: 
case '5': return "금";
case 6: 
case '6': return "토";
case 7: 
case '7': return "일";
}
};

commn.date_add = function(sDate, nDays) {

if(!sDate){

function getToday(){
var date = new Date();
var year = date.getFullYear();
var month = ("0" + (1 + date.getMonth())).slice(-2);
var day = ("0" + date.getDate()).slice(-2);

return year + "-" + month + "-" + day;
}
sDate = getToday();
}
var yy = parseInt(sDate.substr(0, 4), 10);
var mm = parseInt(sDate.substr(5, 2), 10);
var dd = parseInt(sDate.substr(8), 10);

d = new Date(yy, mm - 1, dd + nDays);

yy = d.getFullYear();
mm = d.getMonth() + 1; mm = (mm < 10) ? '0' + mm : mm;
dd = d.getDate(); dd = (dd < 10) ? '0' + dd : dd;

return '' + yy + '-' +  mm  + '-' + dd;
};

commn.toNumber = function(str){

return Number(commn.nvl(str, '0'));
};


$(function(){

Handlebars.registerHelper('numberWithCommas', function(v1) {
if(!v1){
v1 = '0';
}
if(v1 != null && v1 != '') {
return numberWithCommas(v1);
}
return '';
});
Handlebars.registerHelper('ifCond', function(v1, v2, options) {
if(v1 === v2) {
return options.fn(this);
}
return options.inverse(this);
});

Handlebars.registerHelper('formatDate', function(v1, v2, v3, v4) {

if(v1 && v2 && v3 && v4){

var lpad = function(n, width) {
n = n + '';
return n.length >= width ? n : new Array(width - n.length + 1).join('0') + n;
};

return  v1 + v4 + lpad(v2, 2) + v4 + lpad(v3, 2);
}else{
return '';
}
});

var selectedPrd = {};

var $campTab = $('#tab1');

var $campTabBtn = $('[href="#tab1"]').closest('li');

var initPage = function(){

bindEvents();

if($campTabBtn.hasClass('is-active')){

$campTabBtn.trigger('click');
}
};

var refreshDate = function(){

var $info = $campTab.find('[data-area-name="camp-reservation-info"]');
$info
.data('info-period-text', '')
.data('info-period', '')
.data('info-start-date-text', '')
.data('info-end-date-text', '')
.data('info-use-bgn-dtm', '')
.data('info-use-end-dtm', '');

//$info.hide();
$campTab.find('[data-area-name="camp-period-default"]').css('display', '').siblings('[data-area-name="camp-period-selected"]').hide();
$info.find('[data-area-name="camp-period"]').html('');
$info.find('[data-area-name="camp-bgn-dt"]').html('-');
$info.find('[data-area-name="camp-end-dt"]').html('-');

$campTab.find('[data-calendar-cell-yyyy-mm-dd]').removeClass('start end selected');
};

//예약하기
function reservation(){

if(selectedPrd.brfeTerYn == 'Y'){

if(!$campTab.find('[name="rsvtDvcdDs"]:checked').val()){

toastrMsg("자격구분을 선택해주세요.","메세지","e");
$campTab.find('[name="rsvtDvcdDs"]').eq(0).focus();
return;
}
if(!$.trim($campTab.find('[name="dstpRegNo"]').val())){

toastrMsg("장애인등록번호 또는 복지카드발급일자(뒤 3자리)를 입력해주세요.","메세지","e");
$campTab.find('[name="dstpRegNo"]').focus();
return;
}
}

if($campTab.find("input[name=captcha]").val() == null || $campTab.find("input[name=captcha]").val().trim() == "") {
toastrMsg("자동예약방지글을 입력해주세요.","메세지","e");
$campTab.find("input[name=captcha]").focus();
return;
}
closePopup('automatic-character-camp');

const request = new XMLHttpRequest();
request.open('POST', "/reservation/selectCampReserPopYn.do");
let param = new FormData();
let campMountain = selectedPrd.deptId.slice(0, 4);
param.append('mngrDeptCode', campMountain);
request.send(param);
request.onreadystatechange = function() {
if (request.readyState == XMLHttpRequest.DONE) {
const status = request.status;
if (status === 0 || (status >= 200 && status < 400)) {
         if(JSON.parse(request.response).campReserPopYn == 'Y') {
       openPopup('campNoticePopup');
         } else {
           reservationStep2();
         }
} else {
    reservationStep2();
}
}
}
}
function reservationStep2() {
closePopup('campNoticePopup');

commn.callAjax({
url: '/reservation/registerCampReservation.do',
data: {
"prdId" : selectedPrd.prdId
, "deptId" : selectedPrd.deptId
, "useBgnDtm" : selectedPrd.useBgnDtm.replace(/\-/g,'')
, "useEndDtm" : selectedPrd.useEndDtm.replace(/\-/g,'')
, "reserTp" : selectedPrd.reserTp
, "checkPerVal" : selectedPrd.period
/* , "price" : price
, "nextPrice" : next_price */
, "captcha" : $campTab.find("input[name='captcha']").val()
/* , "optAmtTotal" : optAmtTotal */
, "selectedOptions" : selectedPrd.selectedOptions
, 'rsvtDvcd' : selectedPrd.brfeTerYn == 'Y' ? $campTab.find('[name="rsvtDvcdDs"]:checked').val() : ''
, 'dstpRegNo' : selectedPrd.brfeTerYn == 'Y' ? $campTab.find('[name="dstpRegNo"]').val() : ''
},
dataType: 'json'
})
.done(function(result){

//정상 요청, 응답 시 처리 작업
if(result.resultCd == "S"){
$(".btn-close:eq(1)").trigger("click");

var ymdhm = function(value){

if(value){
  var year = value.substring(0, 4);
  var month = value.substring(4, 6);
  var day = value.substring(6, 8);
  var hour = value.substring(8, 10);
  var minute = value.substring(10, 12);
  //var second = value.substring(12, 14);
  return year + '년 ' + month + '월 ' + day + '일 ' + hour + ':' + minute;
}
return '';
};

$('#btnMypage').hide();

if(selectedPrd.reserTp == 'W'){
$campTab.find('[data-area-name="reservation-popup-container-w"]').css('display', '').siblings('[data-area-name="reservation-popup-container"]').hide();
}
else{
$campTab.find('[data-area-name="reservation-popup-container"]').css('display', '').siblings('[data-area-name="reservation-popup-container-w"]').hide();
$campTab.find('[data-popup-information-camp="sttlmMtDtm"]').html(ymdhm(commn.nvl(result.dataMap).sttlmMtDtm2));//결제만기일시

$('#btnMypage').show();
$('#btnMypage').text("결제하기");
$('#btnMypage').prop('href', '/mypage/selectReservationPayment.do?rsvtId='+result.dataMap.rsvtId+'&prdDvcd=C');
}

// 예약안내 레이어팝업
$campTab.find('[data-popup="reservation-information1-camp"]').trigger('click');
}else{
toastrMsg(result.resultMsg,"메세지","e");
      closePopup('automatic-character-camp');
}
})
.fail(function(e){
//$("#loadingImage").hide();
toastrMsg("일시적으로 장애가 발생하였습니다. 잠시 후 다시 시도하여 주시기 바랍니다.","메세지"); //<br />원활한 서비스를 위해 최선을 다하겠습니다.
});
}
document.getElementById("reservationStep2Btn").addEventListener('click', reservationStep2);

var updateStep = function(step){

switch(step) {

case '1':

$('[data-reservation-area="step"]').removeClass('step2').addClass('step1');
$('[data-reservation-area="stepText"]').html('STEP.1');
$campTab.find('[data-reservation-step="2"]').hide();
      $campTab.find('[data-reservation-step="1"]').css('display', '');
      $campTab.find('[data-template-id="camp-btn-area"]').css('display', 'none');
break;

case '2':
$('[data-reservation-area="step"]').removeClass('step1').addClass('step2');
$('[data-reservation-area="stepText"]').html('STEP.2');
$campTab.find('[data-reservation-step="1"]').hide();
$campTab.find('[data-reservation-step="2"]').css('display', '');
      $campTab.find('[data-template-id="camp-btn-area"]').css('display', '');
break;
}
};

var campListBindEvents = function(){


$campTab.find('[name="camp-mountain"]').on('click', function(){

$campTab.find('input[type="checkbox"][data-gubun-dept-id]').prop('checked', false).closest('li').siblings().hide();//유형 hide
$campTab.find('[data-dept-dept-parent-nm]').prop('checked', false).closest('li').hide();
$campTab.find('[data-dept-dept-parent-nm="' + $(this).val() + '"]').closest('li').css('display', '');

refreshDate();
});


$campTab.find('input[type="radio"][data-dept-dept-id]').on('click', function(){

$campTab.find('input[type="checkbox"][data-gubun-dept-id]').prop('checked', false).closest('li').siblings().hide();
$campTab.find('input[type="checkbox"][data-gubun-dept-id="' + $(this).data('dept-dept-id') + '"]').closest('li').css('display', '');

if(!$campTab.find('input[type="checkbox"][data-gubun-dept-id="' + $(this).data('dept-dept-id') + '"]').length){

toastrMsg("현재 조성중인 시설입니다.","메세지");
$campTab.find('[data-area-name="empty-gubun-text"]').css('display', '');
}
refreshDate();
});

/* 달력 click */
$campTab.find('[data-calendar-cell-yyyy-mm-dd]').on('click', function(){

if(!$campTab.find('input[type="radio"][data-dept-dept-id]:checked').length){

toastrMsg("위치를 선택해주세요.","메세지");
return false;
}
var $this = $(this);
var $start = $campTab.find('[data-calendar-cell-yyyy-mm-dd].start.selected'); //입실날짜
var $end = $campTab.find('[data-calendar-cell-yyyy-mm-dd].end.selected'); //퇴실날짜

if($start.length && $end.length){

$campTab.find('[data-calendar-cell-yyyy-mm-dd]').removeClass('start selected end');
$start = $campTab.find('[data-calendar-cell-yyyy-mm-dd].start.selected'); //입실날짜
}

if($this.data('calendar-cell-is-end-dt') == 'Y' && !$start.length){

toastrMsg("해당 날짜는 퇴실일로만 선택 가능합니다.","메세지");
return false;
}

if(!$start.length){
//입실선택전클릭
$this.addClass('start selected');
toastrMsg("이용 기간은 2박 3일 이내로 선택해 주세요.","메세지");
}else{
//입실선택후클릭
var startDate = $start.data('calendar-cell-yyyy-mm-dd');
var endDate = $this.data('calendar-cell-yyyy-mm-dd');

if(startDate.replace(/\-/g,'') >= endDate.replace(/\-/g,'')){
//start보다 작거나 같으면 	
$campTab.find('[data-calendar-cell-yyyy-mm-dd]').removeClass('start selected end');
toastrMsg("입실일 이후로 선택해 주세요.","메세지");
return false;
}

var sdt = new Date(startDate);
var edt = new Date(endDate);
var dateDiff = Math.ceil((edt.getTime()-sdt.getTime())/(1000*3600*24));


if(dateDiff > 2){
//최대 2박3일
$campTab.find('[data-calendar-cell-yyyy-mm-dd]').removeClass('start selected end');
toastrMsg("최대 2박 3일까지 예약 가능합니다.","메세지");
return false;
}

for(var i = 1; i <= dateDiff; i++){
//입실일과 퇴실일 사이 class add
$campTab.find('[data-calendar-cell-yyyy-mm-dd="' + commn.date_add(startDate, i) + '"]').addClass('selected');
}

//퇴실일  class add
$this.addClass('end selected');

var $info = $campTab.find('[data-area-name="camp-reservation-info"]');
var periodText = dateDiff == 1 ? '1박 2일' : '2박 3일';
var startDateText = startDate + ' [' + commn.getDayWeekNm($start.data('calendar-cell-day-week')) + ']';
var endDateText = endDate + ' [' + commn.getDayWeekNm($this.data('calendar-cell-day-week')) + ']';
$info
.data('info-period-text', periodText)
.data('info-period', dateDiff)
.data('info-start-date-text', startDateText)
.data('info-end-date-text', endDateText)
.data('info-use-bgn-dtm', startDate)
.data('info-use-end-dtm', endDate);

//$info.css('display', '');
$campTab.find('[data-area-name="camp-period-default"]').hide().siblings('[data-area-name="camp-period-selected"]').css('display', '');
$info.find('[data-area-name="camp-period"]').html(periodText);
$info.find('[data-area-name="camp-bgn-dt"]').html(startDateText);
$info.find('[data-area-name="camp-end-dt"]').html(endDateText);
}
});
};

window.automaticCharacterCamp = function(){

//drawOptions
var optParam = {};
optParam.prdId = selectedPrd.prdId;
optParam.useBgnDtm = selectedPrd.useBgnDtm.replace(/\-/g,'');
optParam.period = selectedPrd.period;

commn.callAjax({
url: '/reservation/campsite/selectOptionList.do',
data: optParam,
dataType: 'json'
})
.done(function(res){

if(!res.optionList || $.isEmptyObject(res.optionList)){

$('#application-reservation-camp-option [data-popup-btn="confirm"]').trigger('click')
}else{

var $options = $campTab.find('[data-template-id="camp-options-template"]');
var optionsTemplate = Handlebars.compile($('#' + $options.data('template-id')).html()); 

var optTemplateParam = {};
optTemplateParam.options = res.optionList;
optTemplateParam.period = selectedPrd.period;
$options.html(optionsTemplate(optTemplateParam));

$campTab.find('[data-popup="application-reservation-camp-option"]').trigger('click');
}
})
.fail(function(e){
//$("#loadingImage").hide();
toastrMsg("일시적으로 장애가 발생하였습니다. 잠시 후 다시 시도하여 주시기 바랍니다.","메세지"); //<br />원활한 서비스를 위해 최선을 다하겠습니다.
});
};

var bindEvents = function(){

$campTab.find('#automatic-character-camp [data-popup-btn="confirm"]').on('click', reservation);

$campTab.find('#automatic-character-camp [data-popup-btn="cancel"]').on('click', function(){$('#automatic-character-camp .btn-close').trigger('click');});

$campTab.find('#application-reservation-camp-option [data-popup-btn="cancel"]').on('click', function(){$('#application-reservation-camp-option .btn-close').trigger('click');});

$campTab.find('[data-reservation-step="2"]').on('click', '[data-button-name="reservation"]', function(){

selectedPrd = {};
selectedPrd.useBgnDtm = $(this).data('step2-use-bgn-dtm');
selectedPrd.useEndDtm = $(this).data('step2-use-end-dtm');
selectedPrd.periodText = $(this).data('step2-period-text');
selectedPrd.period = $(this).data('step2-period');
selectedPrd.startDateText = $(this).data('step2-start-date-text');
selectedPrd.endDateText = $(this).data('step2-end-date-text');
selectedPrd.prdNm = $(this).data('step2-prd-nm');
selectedPrd.prdId = $(this).data('step2-prd-id');
selectedPrd.deptId = $(this).data('step2-dept-id');
selectedPrd.codeNm2 = $(this).data('step2-code-nm2');
selectedPrd.salAmtSum = commn.nvl($(this).data('step2-sal-amt-sum'), '0');
selectedPrd.salAmtSumCommas = numberWithCommas(selectedPrd.salAmtSum);

selectedPrd.reserTp = $(this).data('step2-reser-tp');

selectedPrd.brfeTerYn = $(this).data('step2-brfe-ter-yn');

commn.callAjax({
'url': '/reservation/auth.do',
/* 'data': param, */
'dataType' : 'json'
})
.done(window.automaticCharacterCamp)
.fail(function(e){

if(e.status == '401'){

loginPopup('window.automaticCharacterCamp();');
}else{

toastrMsg("일시적으로 장애가 발생하였습니다. 잠시 후 다시 시도하여 주시기 바랍니다.","메세지"); //<br />원활한 서비스를 위해 최선을 다하겠습니다.
}
});
});

$('#application-reservation-camp-option [data-popup-btn="confirm"]').on('click', function(){


var $popup = $campTab.find('#automatic-character-camp');
var $popupContainer = $campTab.find('[data-template-id="camp-popup-container-template"]');

var source = $('#' + $popupContainer.data('template-id')).html(); 
var template = Handlebars.compile(source); 

//옵션
var $selectedOptions = $('[data-template-id="camp-options-template"]').find('[type="checkbox"][data-opt-id]:checked');
var optionHtml = '';
var optAmtTotal = 0;
var optIds = '';

$.each($selectedOptions, function(i){

if(i > 0){
optionHtml += '<br>';
}

if(optIds){
optIds += ',';
}

optAmtTotal += Number($(this).val());

optionHtml += $(this).data('opt-nm') + '사용 ' + selectedPrd.period + '박';

optIds += $(this).data('opt-id');
});

selectedPrd.selectedOptions = optIds;
selectedPrd.optionHtml = optionHtml;
selectedPrd.totalAmt = commn.toNumber(selectedPrd.salAmtSum) + optAmtTotal;
selectedPrd.totalAmtCommas = numberWithCommas(selectedPrd.totalAmt);

//무장애영지
if(selectedPrd.brfeTerYn == 'Y'){

var brfeTerDt = selectedPrd.useBgnDtm;
if(selectedPrd.period == 2){

brfeTerDt = commn.date_add(brfeTerDt, 1);
}
brfeTerDt = commn.toNumber(brfeTerDt.replace(/\-/g,''));

if(brfeTerDt < commn.toNumber(commn.date_add('', 3).replace(/\-/g,''))){

selectedPrd.brfeTerYn = 'N';
}
}

$popupContainer.html(template(selectedPrd));

$campTab.find("input[name=captcha]").val('');

$("#pnlRsrImgCamp").html("");
$("#pnlRsrImgCamp").append("<img alt='자동예약 방지문자'/>").find("img:last").attr("src", "/reserCaptcha.do?dummy=" + (new Date()).getTime());

$popup.find(".popup-wrap").css("top", "auto");

$campTab.find('[data-popup="' + $popup.attr('id') + '"]').trigger('click');

$(this).siblings('[data-popup-btn="cancel"]').trigger('click');

$popup.find('.captcha-area input[name="captcha"]').focus();
});

$campTab.find('[data-template-id="camp-popup-container-template"]').on('click', '[data-button-name="exemption-auth"]', function(){

$('[data-popup="exemption-auth"]').trigger('click');
});

$campTab.find('[data-button-name="cancel"]').on('click', function(){

updateStep('1');
});


/* $('input[type="radio"][name="shelterMountain"]').on('click', function(){

$('input[type="radio"][data-dept-id]').closest('li').hide();
$('input[type="radio"][data-dept-id^="' + $(this).val() + '"]').closest('li').css('display', '');
}); */

/* step1 다음단계 click */
$campTab.find('[data-button-name="refresh"]').on('click', function(){

//$campTabBtn.data('active-flag', '').trigger('click');
$campTab.find('[name="camp-reservation2"][value="N"]').prop('checked', true);
$campTab.find('input[type="checkbox"][data-gubun-dept-id]').prop('checked', false).closest('li').siblings().hide();
$campTab.find('[data-dept-dept-parent-nm]').prop('checked', false).closest('li').hide();
$('[name="camp-mountain"]').prop('checked', false);

refreshDate();
});
/* step1 다음단계 click */
$campTab.find('[data-button-name="goStep2"]').on('click', function(){

if(!$campTab.find('[data-calendar-cell-yyyy-mm-dd].start.selected').length
|| !$campTab.find('[data-calendar-cell-yyyy-mm-dd].end.selected').length){
toastrMsg("날짜를 선택해주세요.","메세지");
return false;
}
if(!$campTab.find('[data-gubun-prd-ctg-id]:checked').length){
toastrMsg("유형을 선택해주세요.","메세지");
return false;
}

var $info = $campTab.find('[data-area-name="camp-reservation-info"]');

var campsitesParam = {};
campsitesParam.prdSalStcd = $campTab.find('[name="camp-reservation2"]:checked').val();
campsitesParam.period = $info.data('info-period');
campsitesParam.bgnDate = $campTab.find('[data-calendar-cell-yyyy-mm-dd].start.selected').data('calendar-cell-yyyy-mm-dd').replace(/\-/g,'');
campsitesParam.endDate = $campTab.find('[data-calendar-cell-yyyy-mm-dd].end.selected').data('calendar-cell-yyyy-mm-dd').replace(/\-/g,'');
campsitesParam.deptId = $campTab.find('input[type="radio"][data-dept-dept-id]:checked').data('dept-dept-id');
campsitesParam.prdCtgIds = $("[data-gubun-prd-ctg-id]:checked").map(function(){
return $(this).data('gubun-prd-ctg-id');
}).get().join(',');

commn.callAjax({
'url': '/reservation/campsite/campsites.do',
'data': campsitesParam,
'dataType' : 'json'
})
.done(function(res){

if(!res.avails || $.isEmptyObject(res.avails)){
if(res.prdSalStcd == 'W'){
toastrMsg("선택하신 날짜에 대기가능한 야영장이 없습니다.","메세지");
}else{
toastrMsg("선택하신 날짜에 예약가능한 야영장이 없습니다.","메세지");
}
return false;
}

updateStep('2');
var $prds = $campTab.find('[data-template-id="camp-step2-template"]');
var prdsSource = $('#' + $prds.data('template-id')).html(); 
var prdsTemplate = Handlebars.compile(prdsSource);
var prdsTemplateParam = {};
var $selectedDept = $campTab.find('[data-dept-dept-nm]:checked');

prdsTemplateParam.avails = res.avails;
prdsTemplateParam.deptParentNm = $selectedDept.data('dept-dept-parent-nm');
prdsTemplateParam.deptNm = $selectedDept.data('dept-dept-nm');
prdsTemplateParam.deptId = $selectedDept.data('dept-dept-id');
//$campTab.find('[data-area-name="camp-reservation-info"]')
prdsTemplateParam.periodText = $info.data('info-period-text');
prdsTemplateParam.period = $info.data('info-period');
prdsTemplateParam.startDateText = $info.data('info-start-date-text');
prdsTemplateParam.endDateText = $info.data('info-end-date-text');
prdsTemplateParam.useBgnDtm = $info.data('info-use-bgn-dtm');
prdsTemplateParam.useEndDtm = $info.data('info-use-end-dtm');

prdsTemplateParam.reserTp = $campTab.find('[name="camp-reservation2"]:checked').val() == 'W' ? 'W' : 'R'; 

$prds.html(prdsTemplate(prdsTemplateParam));

$campTab.find('[data-area-name="step2TotalCnt"]').html(commn.nvl(res.avails).length);
$campTab.find('[data-area-name="step2PeriodText"]').html($info.data('info-period-text'));
$campTab.find('[data-area-name="step2StartEndText"]').html($info.data('info-start-date-text') + ' ~ ' + $info.data('info-end-date-text'));

//res.avails.length
})
.fail(function(){

//$("#loadingImage").hide();
toastrMsg("일시적으로 장애가 발생하였습니다. 잠시 후 다시 시도하여 주시기 바랍니다.","메세지"); //<br />원활한 서비스를 위해 최선을 다하겠습니다.
});

});

$campTabBtn.on('click', function(){

var $this = $(this);
var param = {};

if($campTab.find('[data-reservation-step="2"]').css('display') == 'none'){
updateStep('1');
}else{
updateStep('2');
}

if($this.data('active-flag') == 'Y'){
return false;
}
/* param.deptId = $('input[type="radio"][name="shelterMountain"]:checked').val();
param.prdId = $this.val(); */
commn.callAjax({
'url': '/reservation/campsite/campList.do',
'data': param,
'dataType' : 'json'
})
.done(function(res){

$this.data('active-flag', 'Y');

var calendars = commn.nvl(res).calendars;
var campGroupList = commn.nvl(res).campGroupList;
var campGubunList = commn.nvl(res).campGubunList;
var campList = commn.nvl(res).campList;

var $group = $('[data-template-id="camp-group-template"]');
var $dept = $('[data-template-id="camp-dept-template"]');
var $gubun = $('[data-template-id="camp-gubun-template"]');
var $calendars = $('[data-template-id="camp-calendar-template"]');

$group.empty();
if(campGroupList){

var groupTemplate = Handlebars.compile($('#' + $group.data('template-id')).html());

$group.html(groupTemplate(campGroupList));
}

$dept.empty();
if(campList){

var deptTemplate = Handlebars.compile($('#' + $dept.data('template-id')).html());

$dept.html(deptTemplate(campList));
}

$gubun.empty();
if(campGubunList){

var gubunTemplate = Handlebars.compile($('#' + $gubun.data('template-id')).html());

$gubun.html(gubunTemplate(campGubunList));
}

$calendars.find('[data-area-name="camp-calendar"]').remove();
if(calendars){

var source = $('#' + $calendars.data('template-id')).html(); 
var template = Handlebars.compile(source); 

$.each(calendars, function(i, item){

$calendars.find('[data-area-name="camp-reservation-info"]').before(template(item))
.find('[data-calendar-cell-yyyy-mm-dd]').on('click', function(){
});

});
}

campListBindEvents();
})
.fail(function(){

//$("#loadingImage").hide();
toastrMsg("일시적으로 장애가 발생하였습니다. 잠시 후 다시 시도하여 주시기 바랍니다.","메세지"); //<br />원활한 서비스를 위해 최선을 다하겠습니다.
});
});
};

initPage();
});

function recalWithExemption(){

}

//]]>

// 2번째
$(document).ready(function(){

//다음
$('.selfAuthModal').click(function(){

var policyVal = $('input[name="policy"]:checked').val();
if(policyVal  == ''){
toastrMsg('개인정보 제공 동의를 해주세요.');
return false;
}

if($('#usNmId').text() == ''){
toastrMsg('본인인증을 진행해주세요.');
return false;
}

if($('#usNm').val() == ''){
toastrMsg('주민등록번호 뒷자리를 입력해주세요.');
return false;
}
else {
// 주민번호 뒷자리에 다른 정보를 입력하는 경우가 방지.
var check = /^[0-9]+$/; 
if (!check.test($('#usNm').val())) {
toastrMsg("숫자만 입력 가능합니다.");
return false;
}
}

ajaxCall({
  url : "/common/authGpkiForPay.do",
  data : {
      "tgtrNm" : $('#usNmId').text(),
      "trtrNum" : $('#usNumId').text()+""+$('#usNm').val(),
      "authType" : $('#authTypeId').val()
  },
  success : function(dat){
      if( $('#authTypeId').val() == 'A'){ //장애인여부확인
          reductionDisabledDc(dat);
      }else{
          naManMeritDc(dat);
          
          // 2023-03-02 : 세션을 이용하지 않고 국가유공자 코드를 서버에서 세팅하기
          let chagneForm_disabledCode = document.getElementById("chagneForm_disabledCode");
          if (chagneForm_disabledCode != null) {
            chagneForm_disabledCode.value = dat.disabledCode;
          }
          let chagneForm_wondClassCd = document.getElementById("chagneForm_wondClassCd");
          if (chagneForm_wondClassCd != null) {
            chagneForm_wondClassCd.value = dat.wondClassCd;
          }
          let chagneForm_subjKbnCd = document.getElementById("chagneForm_subjKbnCd");
          if (chagneForm_subjKbnCd != null) {
            chagneForm_subjKbnCd.value = dat.subjKbnCd;
          }
      }
  },
  error : function(){
      toastrMsg('감면 인증 중 오류가 발생하였습니다. <br/>관리자에게 문의하여 주세요.');
  }
})
});

//취소 감면인증정보 확인 모달 제거
$('.selfAuthModalCancel').click(function(){
$('#radio1-1').prop('checked',true);
closePopup('exemption-auth');
});

});
function reductionDisabledDc(dat){
var qufyYn = dat.qufyYn;
var disabledCode = dat.disabledCode;
let subTitle = '';
let content = '';
let type = '';

if ($('#usNmId').text() == '') {

if(qufyYn == 'M'){

subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
content = '기존 대상자였지만 현재 비대상자로 전환 되었습니다.<br/>확인 후 다시 시도해주세요.';
type = 'error';
$('#radio1-1').prop('checked', true);

}else if(qufyYn == 'Y') {

if (disabledCode == '00' || disabledCode == '98' || disabledCode == '99') {

  var strMsg = '';
  if (disabledCode == '00') {
      strMsg = '장애 미해당';
  } else if (disabledCode == '98') {
      strMsg = '결정보류';
  } else if (disabledCode == '99') {
      strMsg = '확인불가';
  }

  $('#exemptionAuthText').val('대상자가 아닙니다');
  subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
  content = '현재 '+strMsg+' 상태입니다.<br/>확인 후 다시 시도해주세요.';
  type = 'error';
  $('#radio1-1').prop('checked', true);

} else {

  if ('10' == disabledCode) {
      $('#radio1-2').prop('checked', true);
      $('#certTextId').val('장애인(중증, 1~3급)');
      
      // 예약화면에서 장애인전용상품인 경우
      $('#exemptionAuthText').val('장애인(중증, 1~3급)');
  } else if ('20' == disabledCode) {
      $('#radio1-3').prop('checked', true);
      $('#certTextId').val('장애인(경증, 4~6급)');
      
     // 예약화면에서 장애인전용상품인 경우
      $('#exemptionAuthText').val('장애인(경증, 4~6급)');
  }else{
      $('#radio1-3').prop('checked', true);
      $('#certTextId').val('장애인 대상자');
      
     // 예약화면에서 장애인전용상품인 경우
      $('#exemptionAuthText').val('장애인 대상자');
  }

  subTitle = $('#usNmId').text() + '님은 감면 대상자입니다.';
  content = '';
  type = '';

  //결제금액 재계산
  recalWithExemption();
  
}

} else {

subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
content = '확인 후 다시 시도해주세요.';
type = 'error';
$('#radio1-1').prop('checked', true);

}

} else {

subTitle = '예약자 본인이 아니므로 <br>자격확인을 할 수 없습니다.';
content = '현장 방문 시 증빙을 지참하시고 할인 받으시기 바랍니다.';
type = 'error';
$('#radio1-1').prop('checked', true);

}

alertPopup({
title: '알림',
subTitle: subTitle,
content: content,
type: type
});

/* 
* 간혹 메인창이 닫혀 버리는 듯.
*
try {
self.close();
} catch (e) {
console.log(e);
}
*/

try {
// 예약화면에서 장애인전용상품인 경우
closePopup('exemption-auth');
} catch (e) {
console.log(e);
}

}

function naManMeritDc(dat){
let cnt = dat.cnt;
let dcTargetYn = dat.dcTargetYn;
let relCd = dat.relCd;
let authoriPsnYn = dat.authoriPsnYn;
let wondClassCd = dat.wondClassCd;
let subjKbnCd = dat.subjKbnCd;
let inquRsltCd = dat.inquRsltCd;

let subTitle = '';
let content = '';
let type = '';

if ($('#usNmId').text() == '') {
//조회결과가 있을때
if (cnt > 0) {
//감면대상일때
if(dcTargetYn == 'Y') {
/* Ver1.
  if ('00011' == wondClassCd || '00012' == wondClassCd
      || '00013' == wondClassCd || '00020' == wondClassCd
      || '00030' == wondClassCd || '00G01' == wondClassCd
      || '00G02' == wondClassCd || '00G03' == wondClassCd) { //1~3급

      $('#radio1-4').prop('checked', true);
      $('#certTextId').val('국가유공자(1~3급)');
  } 
  else if ('00017' == subjKbnCd || '00018' == subjKbnCd || '00019' == subjKbnCd) { //518 민주화운동자.
      $('#radio1-5').prop('checked', true);
      $('#certTextId').val('5.18 민주운동자');
  } 
  else { //그 외
      $('#radio1-6').prop('checked', true);
      $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
  }
*/

/*
  결제를 위한 결제금액 계산 부분과 동일하게. : dcAmt()
  
  국가유공자 전체 코드 감면대상으로 적용
   국가유공자(subjKbnCd) 등급값(wondClassCd)이 있으면 등급에 따라
   없으면 등급외로.
 */
var bChk = false;
  if(subjKbnCd != "") {
    // 5.18 유공자 별도 분리
  if ('00017' == subjKbnCd || '00018' == subjKbnCd || '00019' == subjKbnCd) {
    $('#radio1-5').prop('checked', true);
        $('#certTextId').val('5.18 민주운동자');
    
        bChk = true;
  }
    // 나머지는 등급에 따라(등급이 없으면 등급외로)
  else {
    if("00011" == wondClassCd || "00012" == wondClassCd || "00013" == wondClassCd ||		//1급 1항~3항
           "00020" == wondClassCd || "00030" == wondClassCd ||                                  //2급 3급
           "00G01" == wondClassCd || "00G02" == wondClassCd || "00G03" == wondClassCd) {   		//장해 1급~3급
      
      $('#radio1-4').prop('checked', true);
          $('#certTextId').val('국가유공자(1~3급)');
      
          bChk = true;
    }
    else if("00040" == wondClassCd || "00050" == wondClassCd ||                             //4~5급
                "00061" == wondClassCd || "00062" == wondClassCd || "00063" == wondClassCd ||  	//6급1항~3항,
                "00070" == wondClassCd || "00G04" == wondClassCd || "00G05" == wondClassCd || "00G06" == wondClassCd || "00G07" == wondClassCd){	//7급, 장해 4~7급

      $('#radio1-6').prop('checked', true);
          $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
      
          bChk = true;
        }
    else if("00081" == wondClassCd || "00082" == wondClassCd || "00083" == wondClassCd ||  	//고도, 중증도, 경도
                "00510" == wondClassCd || "00511" == wondClassCd || "00512" == wondClassCd || "00513" == wondClassCd || "00514" == wondClassCd || "00580" == wondClassCd || "00590" == wondClassCd || //10~14급, 8급, 9급
                "00G08" == wondClassCd || "00G09" == wondClassCd || "00G10" == wondClassCd || "00G11" == wondClassCd || "00G12" == wondClassCd || "00G13" == wondClassCd || "00G14" == wondClassCd || "90001" == wondClassCd) { // 장해 8~13급 , 등외
      
      $('#radio1-6').prop('checked', true);
          $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
        
      bChk = true;
        }
    else {
      // 대상자이긴하나 등급값이 없는 경우
      $('#radio1-6').prop('checked', true);
          $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
        
      bChk = true;
    }
  }
  }
  else {
    // subjKbnCd 값없이 등급만 오는 경우
    // 등급값도 없으면 대상 외로.
    if("00011" == wondClassCd || "00012" == wondClassCd || "00013" == wondClassCd ||		//1급 1항~3항
         "00020" == wondClassCd || "00030" == wondClassCd ||                                  //2급 3급
         "00G01" == wondClassCd || "00G02" == wondClassCd || "00G03" == wondClassCd) {   		//장해 1급~3급
    
    $('#radio1-4').prop('checked', true);
        $('#certTextId').val('국가유공자(1~3급)');
    
        bChk = true;
  }
  else if("00040" == wondClassCd || "00050" == wondClassCd ||                             //4~5급
              "00061" == wondClassCd || "00062" == wondClassCd || "00063" == wondClassCd ||  	//6급1항~3항,
              "00070" == wondClassCd || "00G04" == wondClassCd || "00G05" == wondClassCd || "00G06" == wondClassCd || "00G07" == wondClassCd){	//7급, 장해 4~7급

    $('#radio1-6').prop('checked', true);
        $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
    
        bChk = true;
      }
  else if("00081" == wondClassCd || "00082" == wondClassCd || "00083" == wondClassCd ||  	//고도, 중증도, 경도
              "00510" == wondClassCd || "00511" == wondClassCd || "00512" == wondClassCd || "00513" == wondClassCd || "00514" == wondClassCd || "00580" == wondClassCd || "00590" == wondClassCd || //10~14급, 8급, 9급
              "00G08" == wondClassCd || "00G09" == wondClassCd || "00G10" == wondClassCd || "00G11" == wondClassCd || "00G12" == wondClassCd || "00G13" == wondClassCd || "00G14" == wondClassCd || "90001" == wondClassCd) { // 장해 8~13급 , 등외
    
    $('#radio1-6').prop('checked', true);
        $('#certTextId').val('국가유공자(4~7급), 등급 외(무공·보훈수훈자, 배우자, 유족 등)');
      
    bChk = true;
      }
  else {
      // 대상아님.
  bChk = false;
  }
  }

if(bChk) {
    //할인금액 재계산
    recalWithExemption();

    subTitle = $('#usNmId').text() + '님은 감면 대상자입니다.';
    content = '';
    type = '';
}
else {
  subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
      content = '확인 후 다시 시도해주세요.';
      type = 'error';
      $('#radio1-1').prop('checked', true);
}
} 
else {
  //조회 결과 (S:성공 이 아닐때 )
  if(inquRsltCd != 'S') {
      subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
      content = '조회 결과가 없습니다.<br/>확인 후 다시 시도해주세요.';
      type = 'error';
      $('#radio1-1').prop('checked', true);
  } 
  else {
      //수권자인지 체크
      if(authoriPsnYn != 'Y') {
          subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
          content = '확인 후 다시 시도해주세요.';
          type = 'error';
          $('#radio1-1').prop('checked', true);
      } 
      else {
          //조회결과가 있고, 수권자인데 본인이 아닌경우
          if(relCd != 'A') {
              subTitle = '본인인 경우에만 선할인 가능합니다.';
              content = '수권자 본인만 할인 가능합니다.<br/>가족 및 배우자이신 경우 증빙을 지참하시고 현장할인 받으시기 바랍니다.';
              type = 'error';
              $('#radio1-1').prop('checked', true);
          } 
          else {
              //이경우는 없긴한데 일단 처리
              subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
              content = '확인 후 다시 시도해주세요.';
              type = 'error';
              $('#radio1-1').prop('checked', true);
          }
      }//수권자 END

  }//조회결과 END

}//감면대상 END
} 
else {
//조회결과가 없을때
subTitle = $('#usNmId').text() + '님은 대상자가 아닙니다.';
content = '확인 후 다시 시도해주세요.';
type = 'error';
$('#radio1-1').prop('checked', true);
}//조회결과 0개 END

} 
else {
subTitle = '예약자 본인이 아니므로 <br>자격확인을 할 수 없습니다.';
content = '현장 방문 시 증빙을 지참하시고 할인 받으시기 바랍니다.';
type = 'error';
$('#radio1-1').prop('checked', true);
}

alertPopup({
title: '알림',
subTitle: subTitle,
content: content,
type: type
});

// 간혹 메인창이 닫히는 듯.
// self.close();
closePopup('exemption-auth');

}
//국가유공자 등급확인

//휴대폰 인증
function goAuth(){

$.ajax({
url:"/pay/checkPlusForPay.do",  
type: "POST", 
dataType: "json",
async : false ,
data: {},
success: function(dat) {

//인증요청 암호화 데이터가 없을 경우 오류발생
if(dat.result.sEncData == ''){
  toastrMsg(dat.result.sRtnMsg);
}else{
  $("#EncodeData").val(dat.result.sEncData);
  window.open('', 'popupChk', 'width=500, height=550, top=100, left=100, fullscreen=no, menubar=no, status=no, toolbar=no, titlebar=yes, location=no, scrollbar=no');
  document.form_chk.target = "popupChk";
  document.form_chk.action = "https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb;jsessionid=EC3CAF914268A91D890289085FA47F16.U2006";
  document.form_chk.submit();
}
},
error: function(e1,e2,e3) {

}
});

}


//아이핀 인증
function goAuthiPin(){

$.ajax({
url:"/pay/iPinForPay.do",  
type: "POST", 
dataType: "json",
async : false ,
data: {},
success: function(dat) {

//인증요청 암호화 데이터가 없을 경우 오류발생
if(dat.result.sEncData == ''){
  toastrMsg(dat.result.sRtnMsg);
}else{
     $("#enc_data").val(dat.result.sEncData);
    window.open('', 'popupIPIN2', 'width=450, height=550, top=100, left=100, fullscreen=no, menubar=no, status=no, toolbar=no, titlebar=yes, location=no, scrollbar=no');
    document.form_ipin.target = "popupIPIN2";
    document.form_ipin.action = "https://cert.vno.co.kr/ipin.cb";
    document.form_ipin.submit();
}
},
error: function(e1,e2,e3) {

}
});

}

