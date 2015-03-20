function task(description, init_state)
{
    this.description = description;
    this.state = init_state;
    this.total = null;
    this.progress = 0;
    this.finished = 0;
    this.associate_elem = null;
}

function grunt(idx)
{
    this.task = null;
}

var this_server = {isalive: true, test:function()
	  {
	      var xmlhttp = new XMLHttpRequest();
	      xmlhttp.open("GET", '/', false);
	      xmlhttp.timeout = 6000;
	      xmlhttp.send();
	      xmlhttp.ontimeout = function(){this.isalive = false;};
	      xmlhttp.onerror = function(){this.isalive = false;};
	  }
		  };

var worker_list = [];
var task_list = [];
var finished_task_list = [];
	      
	      
