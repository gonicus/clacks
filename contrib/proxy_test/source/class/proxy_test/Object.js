qx.Class.define("proxy_test.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
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

    /* Setter method for object values
     * */
    setAttribute: function(name, value){
      if(this.initialized){
        var rpc = proxy_test.io.Rpc.getInstance();
        rpc.cA(function(result, error) {
          console.log(result, error);
          if(error){
            console.log(error.message);
          }
        },"setObjectProperty", this.uuid, name, value);
      }
    },

    /* Wrapper method for object calls
     * */
    callMethod: function(method, func, context){
      var rpc = proxy_test.io.Rpc.getInstance();
      var args = ["dispatchObjectMethod", this.uuid, method].concat(Array.prototype.slice.call(arguments, 3));
      rpc.cA.apply(rpc, [function(result){
          func.apply(context, [result]);
        }, this].concat(args));
    }
  }
});
