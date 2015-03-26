var event_src = new EventSource('/events');

var dict = new Array();
var prev_lastEventId = 0;
var lastEventId = 0;

event_src.onerror = function(e){
    console.log("error"+e);
    console.log(event_src);
}
event_src.addEventListener("update", update_listener, false);

event_src.addEventListener("summary", update_listener, false);


function get_elem(type, name)
{
    var elem = document.getElementById(name);
    if(!elem) {
	elem = document.createElement(type);
	elem.id = name;
    }
    return elem;
}

function task(task_name)
//build a new task object from a task name
{
    this.task_elem = document.createElement('div');
    this.state = 'pending';

    var task_ins = this;
    this.cancel_elem = document.createElement('button');
    this.cancel_elem.className = 'cancel';
    this.cancel_elem.innerHTML = 'X';
    this.cancel_elem.onclick = function(){cancel(task_ins);}
    
    this.pause_toggle_elem = document.createElement('button');
    this.pause_toggle_elem.className = 'pause';
    this.pause_toggle_elem.innerHTML = '||';
    this.pause_toggle_elem.onclick = function(){pause_toggle(task_ins)};


    this.task_elem.appendChild(this.cancel_elem);
    this.task_elem.appendChild(this.pause_toggle_elem);
	
    this.name = task_name;
    this.name_elem = document.createElement('a');
    this.name_elem.className = 'task_name';
    this.name_elem.innerHTML = 'task'+this.name;
    this.task_elem.appendChild(this.name_elem);

    this.size = null;
    //stores the total size
    this.progress = 0;
    //stores the size of finished part
    this.progress_elem = null;
}

function remove_elem(elem)
{
    if(elem)
	elem.parentElement.removeChild(elem);
}
    

task.prototype.destructor = function()
{
    remove_elem(this.task_elem);
}

task.prototype.set_size = function(new_size)
{
    this.size = new_size;
    this.set_progress(this.progress)
}

task.prototype.change_state = function(new_state)
{
    this.state = new_state;
    if(new_state.localeCompare('complete') == 0) {
	this.destructor();
	return;
    }
    document.getElementById(new_state).appendChild(this.task_elem);
    if(new_state.localeCompare('paused') == 0)
	this.pause_toggle_elem.innerHTML = '>';
    else
	this.pause_toggle_elem.innerHTML = '||';
}

task.prototype.set_description = function(description)
{
    this.name_elem.innerHTML = description;
}

task.prototype.set_progress = function(downloaded)
{
    var delta = NaN;
    if(parseInt('0x'+prev_lastEventId) != 0) {
	delta = parseInt('0x'+lastEventId) - parseInt('0x'+prev_lastEventId);
	delta/= 1000000;
	delta = (downloaded-this.progress)/delta;
	var totalSec = ((this.size-downloaded)/delta).toFixed(0);
	delta /=1024;
	delta = delta.toFixed(2);

	var hours = parseInt( totalSec / 3600 );
	var minutes = parseInt( totalSec / 60 ) % 60;
	var seconds = totalSec % 60;
	var left = (hours>0 ? hours + "h ":"") + (hours>0||minutes>0 ? minutes + "min ":"") + seconds+'s';
    }
	
    this.progress = downloaded;
    var percentage = this.progress/this.size;

    if(window.innerWidth >= 1080)
	var len = 200;
    else
	var len = 100;
    
    var prog = parseInt(len*percentage);
    //console.log(percentage, prog);
    if(isNaN(prog) || prog < 0)
	prog = 0;
    var ret = '['+Array(prog+1).join('>')+Array(len-prog+1).join('-')+'] ' + downloaded + ' / '+this.size+'( '+(percentage*100).toFixed(1)+'% )';

    if(this.progress_elem == null) {
	this.progress_elem = document.createElement('p');
	this.task_elem.appendChild(this.progress_elem);
    }
    this.progress_elem.innerHTML = ret;
    if(!isNaN(delta))
	this.progress_elem.innerHTML += ' '+delta+" kB/s, "+left;
    else
	this.progress_elem.innerHTML += ' Estimating ...';
	
}

function update_listener(e)
{
    try {
	var json_data = JSON.parse(e.data);
    }
    catch(err) {
	console.log("error", e.data);
    }
    //console.log(e.data);

    prev_lastEventId = lastEventId;
    lastEventId = e.lastEventId;

    for(var task_key in json_data) {
	if(dict[task_key] == null) 
	    dict[task_key] = new task(task_key);
	    
	//find the entry in the dict
	for(var type_key in json_data[task_key]) {
	    data =json_data[task_key][type_key];
	    //console.log(type_key, data);
	    if(type_key.localeCompare('state') == 0) {
		dict[task_key].change_state(data);
		if(data.localeCompare('complete') == 0)
		   delete dict[task_key];
	    }

	    else if(type_key.localeCompare('size') == 0) 
		dict[task_key].set_size(parseInt(data));
	    else if(type_key.localeCompare('progress') == 0) 
		dict[task_key].set_progress(parseInt(data));
	    else if(type_key.localeCompare('description') == 0) 
		dict[task_key].set_description(data);
	    else
		console.log('unknown data:'+ e.data);
	}
    }
}

function submit(path, content, req_name)
{
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open('POST',path, true);
    xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    xmlhttp.overrideMimeType('text/plain');
    xmlhttp.timeout = 5000;

    content = encodeURIComponent(content.trim());
	
    var param = req_name+'='+content;
    xmlhttp.send(param);
    xmlhttp.onreadystatechange = function(){
    	if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
    	    submit_form_responsive = false;
    	}

    }
}

function pause_toggle(taskins)
{
    //console.log('pause_toggle', taskins, taskins.state);
    if(taskins.state.localeCompare('paused') == 0) 
	submit('/', taskins.name, 'resume');
    else 
	submit('/', taskins.name, 'pause');
}

function cancel(taskins)
{
    submit('/', taskins.name, 'cancel');
}

