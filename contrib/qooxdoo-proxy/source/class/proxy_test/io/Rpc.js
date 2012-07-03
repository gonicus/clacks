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
        if(this.queue.length){
          var item = this.queue.pop();
          this.callAsync.apply(this, [item['callback']].concat(item['arguments']));
        }
        if(this.queue.length){
          this.process_queue();
        }
      }
    },

    cA : function(func, context) {
      
      // Create argument list
      var argx = Array();
      for (var e=2; e<arguments.length; e++) {
        argx.push(arguments[e]);
      }
  

      var cl = this;
      var call = {};
      call['arguments'] = argx;
      call['context'] = context;
      call['callback'] = function(result, error){
              if(error){
                if(error.code == 401){
                  cl.running = false;
                  var dialog = new proxy_test.ui.LoginDialog();
                  dialog.open();
                  dialog.addListener("login", function(e){
                      cl.queue.push(call);
                      cl.process_queue();
                    }, cl);
                }else{
                  console.log(error);
                }
              }else{
                cl.running = false;
                cl.process_queue();
                func.apply(call['context'], [result, error]);
              }
            };     
      this.queue.unshift(call);
      this.process_queue();
    }
  }
});
