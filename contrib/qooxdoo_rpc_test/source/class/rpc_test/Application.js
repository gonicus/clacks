/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(rpc_test/*)

************************************************************************ */

/**
 * This is the main application class of your custom application "rpc_test"
 */
qx.Class.define("rpc_test.Application",
{
  extend : qx.application.Standalone,



  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
    /**
     * This method contains the initial application code and gets called 
     * during startup of the application
     * 
     * @lint ignoreDeprecated(alert)
     */
    main : function()
    {
      // Call super class
      this.base(arguments);

      // Enable logging in debug variant
      if (qx.core.Environment.get("qx.debug"))
      {
        // support native logging capabilities, e.g. Firebug for Firefox
        qx.log.appender.Native;
        // support additional cross-browser console. Press F7 to toggle visibility
        qx.log.appender.Console;
      }

      /*
      -------------------------------------------------------------------------
        Below is your actual application code...
      -------------------------------------------------------------------------
      */

      // Document is the application root
      var doc = this.getRoot();

      // Create WebSocket
      var ws_uri = "wss://amqp.intranet.gonicus.de:9000";
      if ("WebSocket" in window) {
          webSocket = new WebSocket(ws_uri);
      }else {
          webSocket = new MozWebSocket(ws_uri);
      }
      this.debug(webSocket);

      var rpc = new qx.io.remote.Rpc("https://amqp.intranet.gonicus.de/rpc", "GOsa JSON-RPC service");
      rpc.setTimeout(10000);
      res = rpc.callSync('login','cajus','tester');

      var button2 = new qx.ui.form.Button("Test Wss", "rpc_test/test.png");
      doc.add(button2, {left: 200, top: 50});
      button2.addListener("execute", function(e) {
            webSocket.send("Hello from JavaScript!");
      });

      var label = new qx.ui.basic.Label("... nothing yet");
      doc.add(label, {left: 400, top: 50});
      webSocket.onmessage = function(e) {
          label.setValue(e.data);
      }

      // Remote table model
      var tableModel = new rpc_test.MyModel();
      tableModel.setColumns( [ "First name", "Last name", "Username" ], [ "givenName", "sn", "uid" ]);
      tableModel.setBlockSize(20);
      var custom = {
        tableColumnModel : function(obj) {
          return new qx.ui.table.columnmodel.Resize(obj);
        }
      };

      var table = new qx.ui.table.Table(tableModel,custom);
      var col = table.getTableColumnModel().getBehavior();
      doc.add(table, {left: 10, top: 100, right: 10});

    }
  }
});
