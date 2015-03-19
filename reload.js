var has_active_task;
var interval_num = false;
var received_etag = 0;
var long_polling_timeout = 60000;

get_update_json('grunt_status.json', grunt_status_onload_callback, true);
function server_is_alive()
{
    var xmlhttp = new XMLHttpRequest();
    var isalive = true;
    xmlhttp.open("GET", 'progress.json', true);
    xmlhttp.timeout = 6000;
    xmlhttp.send()
    xmlhttp.ontimeout=function(){isalive = false;}
    return isalive;
}

function check_ongoing_progress()
{
    if(has_active_task && !interval_num) {
	get_update_json('progress.json', progress_callback, false);//start right away
	interval_num = setInterval(function(){get_update_json('progress.json', progress_callback, false)}, 1000); 
    }
    else if(!has_active_task && interval_num) {
	clearInterval(interval_num);
	interval_num = false;
	get_update_json('progress.json', progress_callback, false);//call it one last time
    }
}

function get_update_json(filename, callback, etag)
{
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", filename, true);
    if(etag) 
	xmlhttp.setRequestHeader('ETag', received_etag);
    xmlhttp.send();
    console.log(filename, xmlhttp);
    xmlhttp.onreadystatechange = function(){callback(xmlhttp);};
}

function get_update_json_timeout(filename, callback, etag, timeout)
{
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", filename, true);
    if(etag) 
	xmlhttp.setRequestHeader('ETag', received_etag);
    xmlhttp.timeout = timeout;
    xmlhttp.send();
    console.log(filename, xmlhttp);
    xmlhttp.onreadystatechange = function(){callback(xmlhttp);};
    xmlhttp.ontimeout=function(){console.log('request timeout, this should not have happened. check if the server is alive.');};
}

//need to check the status when finishes loading anyhow
function grunt_status_onload_callback(xmlhttp)
{
    has_active_task = false;
    if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("grunt_status");
	received_etag = xmlhttp.getResponseHeader('ETag')
	console.log(received_etag)
	//its guaranteed to be ahead of the current etag
	
	for(var i = 0; i < elems.length; i++) {
	    var item = elems[i];

	    if(json[i].length < 1) 
		item.innerHTML = " > Sleeping.";
	    else {
		has_active_task = true;
		item.innerHTML = json[i];
	    }
	}
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
    }
    else if(xmlhttp.readyState != 4)
	has_active_task = false;
    check_ongoing_progress();
}

//long polling
function grunt_status_update_callback(xmlhttp)
{
    if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("grunt_status");
	received_etag = xmlhttp.getResponseHeader('ETag')
	console.log(received_etag)
	has_active_task = false;
	for(var i = 0; i < elems.length; i++) {
	    var item = elems[i];

	    if(json[i].length < 1) 
		item.innerHTML = " > Sleeping.";
	    else {
		has_active_task = true;
		item.innerHTML = json[i];
	    }
	}
	check_ongoing_progress();//test if we should active progress update
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
    } else if(xmlhttp.status == 404) {
	//nothing happened, just timed out
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
	console.log("404 received. No new update.");
    }

    else {
	//something is wrong, better stop progress 
	if(!server_is_alive()) {
	    has_active_task = false;
	    check_ongoing_progress();
	    console.log('The server is dead. BibleThump.');
	}
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
    }
}


function progress_callback(xmlhttp)
{
    if(xmlhttp.readyState==4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("progress");
	for(var i = 0; i < elems.length; i++)
	{
	    var item = elems[i];
	    if(json[i].length < 1) {
		item.innerHTML = "Grunt "+i+": ";
	    }
	    else {
		has_active_task = true;
		var finished = parseInt(json[i][0]);
		var total = parseInt(json[i][1]);
		var percentage = (finished/total*100).toFixed(2);
		item.innerHTML = "Grunt "+i+": "+finished+' / '+total+'('+percentage+'%)';
	    }
	}
    }
}

				   

