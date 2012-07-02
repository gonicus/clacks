qx.Class.define("proxy_test.io.Rpc", {

  type: "singleton",

  extend: qx.io.remote.Rpc,

  construct: function(){
    this.base(arguments);
    this.setUrl(proxy_test.Config.url);
    this.setServiceName(proxy_test.Config.service);
    this.setTimeout(proxy_test.Config.timeout);
  },

  members: {
  
    queue: [],
    running: false,

    process_queue: function(){
      if(!this.running){
        this.running = true;
        this.debug("started next rpc job (queue: " + this.queue.length + ")");
        if(this.queue.length){
          var item = this.queue.pop();
          this.callAsync.apply(this, [item['callback']].concat(item['arguments']));
        }
      }
    },

    cA : function(func, context) {
      
      // Create argument list
      var argx = Array.prototype.slice.call(arguments, 2);

      var cl = this;
      var call = {};
      call['arguments'] = argx;
      call['context'] = context;

      // This is the method that gets called when the rpc is processed
      call['callback'] = function(result, error){

          // Check return codes first. 
          if(error){

            // Permission denied - show login screen to allow to log in.
            if(error.code == 401){
              var dialog = new proxy_test.ui.LoginDialog();
              dialog.open();
              dialog.addListener("login", function(e){
                  cl.queue.push(call);
                  cl.running = false;
                  cl.process_queue();
                }, cl);
            }else{
              cl.running = false;
              this.debug("unhandled error-code: " + error.code);
              console.log(error);
            }
          }else{

            // Everthing went fine, now call the callback method with the result.
            cl.running = false;
            func.apply(call['context'], [result]);

            // Start next rpc-job
            cl.process_queue();
          }
        };    

      // Insert the job into the job-queue and trigger processing.
      this.queue.unshift(call);
      this.debug("added new job to the queue (queue: " + this.queue.length + ")");
      this.process_queue();
    }
  }
});
