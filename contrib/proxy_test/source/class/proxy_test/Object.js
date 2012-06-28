qx.Class.define("proxy_test.Object", {

  extend: qx.core.Object,

  construct: function(data){
    this.base(arguments);

    // Initialize object values
    this.initialized = false;
    this.uuid = data["__jsonclass__"][1][1];
    for(var item in this.attributes){
      if(this.attributes[item] in data){
        this.set(this.attributes[item], data[this.attributes[item]]);
      }
    }

    // Initialization is done (Start sending attribute modifications to the backend)
    this.initialized = true;
  },

  members: {
    initialized: null,

    setAttribute: function(name, value){
      if(this.initialized){
        this.rpc.callAsync(function(result, error) {
          console.log(result, error);
          if(error){
            console.log(error.message);
          }
        },"setObjectProperty", this.uuid, name, value);
      }
    },

    callMethod: function(){
      var args = ["dispatchObjectMethod", this.uuid].concat(Array.prototype.slice.call(arguments, 0));
      return(this.rpc.callSync.apply(this.rpc, args));
    }
  }
});
