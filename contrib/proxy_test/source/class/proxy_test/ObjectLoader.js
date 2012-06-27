qx.Class.define("proxy_test.ObjectLoader", {

  extend: qx.core.Object,

  construct: function(){
    this.base(arguments);

    if(!proxy_test.ObjectLoader.classes){
      proxy_test.ObjectLoader.classes = {}
    }
  },

  statics: {
    classes: null
  },

  members: {

    openObject: function(dn){

      // Add an event listener
      var rpc = proxy_test.io.Rpc.getInstance();
      var result = rpc.callSync("openObject", "object", dn);
      var jDefs = result["__jsonclass__"][1];
      var uuid = jDefs[1];
      var methods = jDefs[3];
      var attributes = jDefs[4];
      var baseType = rpc.callSync("dispatchObjectMethod", uuid, "get_base_type");
      var extensionTypes = rpc.callSync("dispatchObjectMethod", uuid, "get_extension_types");
      var className = "objects." + baseType;

      // Create a metaclass for this type of objects
      if(!(className in proxy_test.ObjectLoader.classes)){

        // The base member variables for the metaclass
        var members = {
            rpc: rpc,
            uuid: null,
            methods: methods,
            attributes: attributes,
            baseType: baseType,
            extensionTypes: extensionTypes
          };


        // this closure returns a new apply method for the given attribute.
        var getApplyMethod = function(name){
          var func = function(value){
            this.setAttribute(name, value);
          };
          return(func);
        }

        // this closure returns a new wrapper-method for an object method
        var getMethod = function(name){
          var func = function(){
            return(this.callMethod.apply(this, [name].concat(Array.prototype.slice.call(arguments))));
          };
          return(func);
        }

        // Create list of properties
        var properties = {};
        for(var attr in attributes){
          var name = attributes[attr];
          var upperName = name.charAt(0).toUpperCase() + name.slice(1);
          var applyName = "_apply_" + upperName;
          var prop = {apply: applyName, event: "changed" + upperName, nullable: true};
          members[applyName] = getApplyMethod(name);
          properties[name] = prop;
        }

        // Create methods
        for(attr in methods){
          var name = methods[attr];
          members[name] = getMethod(name);
        }

        // Create meta class for this object
        var def = {extend: proxy_test.Object, members: members, properties: properties};
        proxy_test.ObjectLoader.classes[className] = qx.Class.define(className, def);
      }

      return(new proxy_test.ObjectLoader.classes[className](result));
    }
  }
});
