qx.Class.define("proxy_test.Config", {

  type: "static",

  statics: {
    url: "https://dyn-167.intranet.gonicus.de/rpc",
    service: "Clacks JSON-RPC service",
    timeout: 60000,
    user: "agent",
    password: "secret"
  }
});
