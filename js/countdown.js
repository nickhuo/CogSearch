/*
Author: Robert Hashemian
http://www.hashemian.com/

You can use this code in any manner so long as the author's
name, Web address and this disclaimer is kept intact.
********************************************************
Usage Sample:

<script language="JavaScript">
TargetDate = "12/31/2020 5:00 AM";
BackColor = "palegreen";
ForeColor = "navy";
CountActive = true;
CountStepper = -1;
LeadingZero = true;
DisplayFormat = "%%D%% Days, %%H%% Hours, %%M%% Minutes, %%S%% Seconds.";
FinishMessage = "It is finally here!";
</script>
<script language="JavaScript" src="http://scripts.hashemian.com/js/countdown.js"></script>
*/


/*
20150314 Modify for Dynamic Target Date
For this study, some pages do not require a timer. 
For example, there's no time limit when participants answer questions on task_c# and k# pages.
Hence, there is no static target date.
The new code reads the remaining seconds from PHP, 
and displays the countdown timer. 
The new code also reads the redirect page from PHP.
For task_b, it redirects users to task_c1.
For task_a, it redirects users to k1.
*/

function calcage(secs, num1, num2) {
  s = ((Math.floor(secs/num1))%num2).toString();
  if (LeadingZero && s.length < 2)
    s = "0" + s;
  return "<b>" + s + "</b>";
}

function CountBack(secs) {
  if (secs < 0) {
	//20150314 Use dynamic redirect page reads from PHP 	
	alert('Time is Up!');
	location.href= RedirectPage;

	return;
  }
  DisplayStr = DisplayFormat.replace(/%%D%%/g, calcage(secs,86400,100000));
  DisplayStr = DisplayStr.replace(/%%H%%/g, calcage(secs,3600,24));
  DisplayStr = DisplayStr.replace(/%%M%%/g, calcage(secs,60,60));
  DisplayStr = DisplayStr.replace(/%%S%%/g, calcage(secs,1,60));

  document.getElementById("cntdwn").innerHTML = DisplayStr;
  if (CountActive)
    setTimeout("CountBack(" + (secs+CountStepper) + ")", SetTimeOutPeriod);
}

function putspan(backcolor, forecolor) {
 document.write("<span id='cntdwn' align='center' style='background-color:" + backcolor + 
                "; color:" + forecolor + "'></span>");
}

if (typeof(BackColor)=="undefined")
  BackColor = "white";
if (typeof(ForeColor)=="undefined")
  ForeColor= "black";
/* 20150314 Don't need TargetDate, 
use RemainingTime instead
if (typeof(TargetDate)=="undefined")
  TargetDate = "12/31/2020 5:00 AM";
*/
if (typeof(DisplayFormat)=="undefined")
  DisplayFormat = "%%D%% Days, %%H%% Hours, %%M%% Minutes, %%S%% Seconds.";
if (typeof(CountActive)=="undefined")
  CountActive = true;
if (typeof(FinishMessage)=="undefined")
  FinishMessage = "";
if (typeof(CountStepper)!="number")
  CountStepper = -1;
if (typeof(LeadingZero)=="undefined")
  LeadingZero = true;

if (typeof(RemainingTime)!="number")
  RemainingTime = 300;
//20150314 Add Redirect Page
if(typeof(RedirectPage)=="undefined")
   RedirectPage="task_c1.php";

CountStepper = Math.ceil(CountStepper);
if (CountStepper == 0)
  CountActive = false;
var SetTimeOutPeriod = (Math.abs(CountStepper)-1)*1000 + 990;
putspan(BackColor, ForeColor);

/* Use Remaining Time
var dthen = new Date(TargetDate);
var dnow = new Date();
if(CountStepper>0)
  ddiff = new Date(dnow-dthen);
else
  ddiff = new Date(dthen-dnow);

gsecs = Math.floor(ddiff.valueOf()/1000);
*/
ddiff=RemainingTime;
gsecs=Math.floor(RemainingTime);
CountBack(gsecs);
