qx.Class.define("proxy_test.io.Rpc", {

  type: "singleton",

  extend: qx.io.remote.Rpc,

  construct: function(){
    this.base(arguments);
    this.setUrl(proxy_test.Config.url);
    this.setServiceName(proxy_test.Config.service);
    this.setTimeout(proxy_test.Config.timeout);
    this.callSync("login", proxy_test.Config.user, proxy_test.Config.password);
  }
});
