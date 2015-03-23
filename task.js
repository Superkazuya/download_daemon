var event_src = new EventSource('/events');

var dict = new Array();

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

    this.name = task_name;
    this.name_elem = document.createElement('p');
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
}

task.prototype.change_state = function(new_state)
{
    this.state = new_state;
    if(new_state.localeCompare('complete') == 0)
	this.destructor();
    else
	document.getElementById(new_state).appendChild(this.task_elem);
}

task.prototype.set_description = function(description)
{
    this.name_elem.innerHTML = description;
}

task.prototype.set_progress = function(downloaded)
{
    var percentage = downloaded/this.size;

    if(window.innerWidth >= 1080)
	var len = 200;
    else
	var len = 100;
    
    var prog = parseInt(len*percentage);
    //console.log(percentage, prog);
    if(isNaN(prog))
	prog = 0;
    var ret = '['+Array(prog+1).join('>')+Array(len-prog+1).join('-')+'] ' + downloaded + ' / '+this.size+'( '+(percentage*100).toFixed(1)+'% )';

    if(this.progress_elem == null) {
	this.progress_elem = document.createElement('p');
	this.task_elem.appendChild(this.progress_elem);
    }
    this.progress_elem.innerHTML = ret;
}

function update_listener(e)
{
    //console.log(">>> "+e.lastEventId);
    try {
	var json_data = JSON.parse(e.data);
    }
    catch(err) {
	console.log("error", e.data);
    }

    for(var task_key in json_data) {
	if(dict[task_key] == null) 
	    dict[task_key] = new task(task_key);
	    
	//find the entry in the dict
	for(var type_key in json_data[task_key]) {
	    data =json_data[task_key][type_key];
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
