
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
    //xmlhttp.ontimeout = alive_report;
    return false;
}
