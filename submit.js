var submit_form_responsive = true;

function display_message(msg_field, msg)
{
    var elem = document.getElementById(msg_field);
    elem.innerHTML = msg;
    //parent_elem.appendChild(elem);
    setTimeout(function(){display_message(msg_field, '')}, 5000);
}

function submit_request()
{
    if(submit_form_responsive) {
	submit_form('/', 'request_input');
	setTimeout(function(){submit_form_responsive = true;}, 3000);
    }
    else
	display_message('response_msg', 'Plz no spammerino');

}

function submit_form(path, id)
{
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open('POST',path, true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.overrideMimeType('text/plain');
    xmlhttp.timeout = 5000;
    var response_msg = document.getElementById('response_msg');
    var content = encodeURIComponent(document.getElementById(id).value.trim());
    if(content.length < 1)
	display_message('response_msg', 'Nothing to submit.');
    else
	display_message('response_msg', 'Submitting ...');
	
    var param = document.getElementById(id).name+'='+content;
    xmlhttp.send(param);
    xmlhttp.onreadystatechange = function(){
    	if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
    	    display_message('response_msg', xmlhttp.responseText);
    	    submit_form_responsive = false;
    	}

    }
}

