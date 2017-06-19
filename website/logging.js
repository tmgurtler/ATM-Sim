var indirizzo = window.location.href.split('/');
var volunteerId = "{{ uid }}";
var pwdToCheck = "";
var sessionType = "Training";

if (localStorage.getItem("attempt") === null)
    localStorage.setItem("attempt", 1);

var c_a = localStorage.getItem("attempt");

switch(true) {
    case c_a < 4:
    pwdToCheck = "jillie02";
    break;

    case c_a < 7:
    pwdToCheck = "william1";
    break;

    case c_a < 10:
    pwdToCheck = "123brian";
    break;

    case c_a < 13:
    pwdToCheck = "lamondre";
    break;

    default:
    window.location.replace("http://tgurtler.pythonanywhere.com/over");
}

document.getElementById("typeToContinue").innerHTML = pwdToCheck;
document.getElementById("email-display").innerHTML = volunteerId;
document.getElementById("session").innerHTML = sessionType;

function printAlerts() {
    var success = document.getElementById("success-alert");
    var error = document.getElementById("error-alert");
    var curl = window.location.href;
    if (curl.indexOf('?') == -1){
         //do nothing
    }
    else {
        curl = curl.split('?')[1]
        console.log(curl)
        if (curl[curl.length-1] == "1") {
            success.style.visibility = "visible";
        }
        else {
            success.style.display = "none";
            error.style.display = "block";
        }
    }
}

var model = '{ "id": "uuid",' +
' "password": "pwd",'+
' "attempt": "0",'+
' "keystrokes": [] }';

var charcounter = 0;
message = JSON.parse(model);

function start() {
    //startTime();
    printAttempt();
    printAlerts();
}

function getTime(event) {
    var x = Date.now();

    if (event.keyCode != 16) {
        document.getElementById("textLog").innerHTML += (x + " ");
    }
}

function getKey(event) {
    document.getElementById("textLog").innerHTML += (String.fromCharCode(event.keyCode) + "\n");
    if (event.keyCode != 13) {
        if (event.key != pwdToCheck[charcounter]) {
            charcounter +=1;
            checkPWD();
        }

        charcounter += 1;
        console.log(charcounter);
    }
}

function checkPWD () {
    if (document.getElementById("Passwd").value == pwdToCheck && charcounter == 8) {
        //alert("The password is correct!");
        
        /*************************UPDATE COUNTER*********************/

        var tent = parseInt(document.getElementById("attempt").innerHTML);
        tent = tent + 1;
        localStorage.setItem("attempt", tent);

        var header = "\nSession: " + document.getElementById("session").innerHTML + " - " + "Attempt: " + document.getElementById("attempt").innerHTML + "\n" ;

        appendToStorage("timestamp", header);
        appendToStorage("timestamp", document.getElementById("textLog").value);

        c = document.getElementById("textLog").value;
        c = c.split('\n');
        c.pop(c.length-1); //this line is empty anyways, so get rid of it
        //c.pop(c.length-1); //rimuove riga con il timestamp del tasto invio
        
        for (var i = 0; i < c.length-1 ; i++) {
            keystroke = c[i].split(" ");
            message['keystrokes'].push({"timestamp": keystroke[0], "key": keystroke[1]})
        }

        message['id']=document.getElementById("email-display").innerHTML;
        message['password']=document.getElementById("Passwd").value;
        message['attempt']=document.getElementById("attempt").innerHTML;
        message = JSON.stringify(message);

        var http = new XMLHttpRequest();
        var url = "https://tgurtler.pythonanywhere.com/save/" + message;
        console.log(url);
        http.open("GET", url, true);
        //http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        http.onreadystatechange = function() { //Call a function when the state changes.
            if(http.readyState == 4 && http.status == 200) {
                var curl = window.location.href;
                if (curl.indexOf('?') == -1) {
                    //do nothing
                }
                else {
                    curl = curl.split('?')[0];
                }

                window.location.href = curl +'?last=1';
                //location.reload();
            }
        }

        http.send();
    }
    else {
        var curl = window.location.href;
        if (curl.indexOf('?') == -1){
            //do nothing
        }
        else {
            curl = curl.split('?')[0]
        }

        //alert("Wrong password!");
        window.location.href = curl+'?last=0';
        //location.reload();
    }
}

function startTime() {
    var today = new Date();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    var day = today.getDate();
    var month = today.getMonth() + 1;
    var year = today.getFullYear();
    m = checkTime(m);
    s = checkTime(s);
    document.getElementById('timeLbl').innerHTML = day + "/" + month + "/" + year + " - " + h + ":" + m + ":" + s;
    var t = setTimeout(startTime, 500);
}

function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }

    return i;
}

function convert() {
    var lines = document.getElementById("textLog").innerHTML.split('\n');
    document.getElementById("textLog").innerHTML="";
    for(var i = 0;i < lines.length-1;i++) {
        var subline = lines[i].split(' ');

        if (i==0) {
            var first=subline[0];
        }

        lines[i] = subline[0]- first + '\t' + subline[1] + '\n';
        document.getElementById("textLog").innerHTML += lines[i];
    }
}

document.getElementById("Passwd").addEventListener("keyup", function(event) {
    event.preventDefault();
    if (event.keyCode == 13) {
        document.getElementById("signIn").click();
    }
});

function printAttempt() {
    if (localStorage.getItem("attempt") === null) {
        localStorage.setItem("attempt", 1);
    }
    else {
        document.getElementById("attempt").innerHTML = localStorage.getItem("attempt");
    }
}

function appendToStorage(name, data) {
    var old = localStorage.getItem(name);
    if(old === null) {
        old = "";
    }
    localStorage.setItem(name, old + data);
}

function clearLS() {
    localStorage.clear();
    location.reload();
}