var has_active_task;
var interval_num = false;
var received_etag = 0;
var long_polling_timeout = 120000;
var minimal_update_request_interval = 1000;

get_update_json('grunt_status.json', grunt_status_onload_callback, true);
function server_is_alive()
{
    var xmlhttp = new XMLHttpRequest();
    var isalive = true;
    xmlhttp.open("GET", 'progress.json', true);
    xmlhttp.timeout = 6000;
    xmlhttp.send()
    xmlhttp.ontimeout=function(){isalive = false;}
    xmlhttp.onreadystatechange = function(){
	if(xmlhttp.readyState == 5)
	    return xmlhttp.status == 200;
    }
    return isalive;
}

function alive_report()
{
    console.log('request timeout, this should not have happened. check if the server is alive.');
    if(!server_is_alive()) {
	has_active_task = false;
	if(interval_num)
	    clearInterval(interval_num);
	console.log('The server is dead. BibleThump.');
	}
    else
	console.log('Server is alive. Yay.');
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
    xmlhttp.onreadystatechange = function(){callback(xmlhttp);};
    xmlhttp.ontimeout=alive_report;
}

//need to check the status when finishes loading anyhow
function grunt_status_onload_callback(xmlhttp)
{
    has_active_task = false;
    if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("grunt_status");
	console.log(response_text)
	received_etag = xmlhttp.getResponseHeader('ETag')
	//its guaranteed to be ahead of the current etag
	
	//pending
	for(var i = 0; i < elems.length; i++) {
	    var item = elems[i];

	    if(json[0][i].length < 1) 
		item.innerHTML = " > Sleeping.";
	    else {
		has_active_task = true;
		item.innerHTML = json[0][i];
	    }
	}
	elems = document.getElementById('pending');
	if(json[1].length < 1)
	    elems.innerHTML = '<p>Nothing pending.</p>';
	else {
	    elems.innerHTML = '';
	    for(var i = 0; i < json[1].length; i++)
		elems.innerHTML += '<p>'+json[1][i]+'</p>';
	}
	    
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
    }
    //else if(xmlhttp.readyState != 4)
	//has_active_task = false;
    //check_ongoing_progress();
}

//long polling
function grunt_status_update_callback(xmlhttp)
{
    if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("grunt_status");
	received_etag = xmlhttp.getResponseHeader('ETag')
	has_active_task = false;
	console.log(response_text)
	for(var i = 0; i < elems.length; i++) {
	    var item = elems[i];

	    if(json[0][i].length < 1) 
		item.innerHTML = " > Sleeping.";
	    else {
		has_active_task = true;
		item.innerHTML = json[0][i];
	    }
	}
	//pending
	elems = document.getElementById('pending');
	if(json[1].length < 1) {
	    elems.innerHTML = '<p>Nothing pending.</p>';
	    elems.innerHTML += json[1];
	}
	else {
	    elems.innerHTML = '';
	    for(var i = 0; i < json[1].length; i++)
		elems.innerHTML += '<p>'+json[1][i]+'</p>';
	}

	check_ongoing_progress();//test if we should active progress update
	setTimeout(function(){get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);},  minimal_update_request_interval);
	//not respond for 1s, there could be too many events
    } else if(xmlhttp.status == 100) {
	//nothing happened, just timed out
	get_update_json_timeout('grunt_status.json', grunt_status_update_callback, true, long_polling_timeout);
	console.log("100 received. No new update.");
    }
}


function progress_callback(xmlhttp)
{
    if(xmlhttp.readyState==4 && xmlhttp.status == 200) {
	var response_text = xmlhttp.responseText;
	var json = JSON.parse(response_text);
	var elems = document.getElementsByClassName("progress");
	//has_active_task = false;
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
		var len;
		if(window.innerWidth > 1080) 
		    len = 200;
		else
		    len = 100;

		var prog = parseInt(len*percentage/100);
		if(isNaN(prog))
		    prog = 0;
		item.innerHTML += '['+ Array(prog+1).join('>')+Array(len-prog+1).join('-')+']';

	    }
	}
    }
}

/*-------------------------------------------------------------------------------------------------------------------------*/
function submit_request()
{
    return submit_form('', 'request_input');
}
function submit_form(path, id)
{
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open('POST',path, true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.timeout = 5000;
    console.log(xmlhttp);
    var response_msg = document.getElementById('response_msg');
    var content = encodeURIComponent(document.getElementById(id).value);
    if(content.length < 1)
    {
	response_msg.innerHTML = 'No request to submit.';
	return false
    }
    else
	response_msg.innerHTML = 'Submitting ...';
	
    var param = "request="+content;
    xmlhttp.send(param);
    xmlhttp.onreadystatechange = function(){
	if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
	    response_msg.innerHTML = xmlhttp.responseText;
	}

    }
    xmlhttp.ontimeout = alive_report;
    return false;
}
