/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(proxy_test/*)

************************************************************************ */

/**
 * This is the main application class of your custom application "proxy_test"
 */
qx.Class.define("proxy_test.Application",
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

      var rpc = proxy_test.io.Rpc.getInstance();
      rpc.cA(function(result, error){
          console.log("Yeah");
        }, this, "openObject", "object", "cn=test test,ou=people,dc=example,dc=net");

      //var proxy = new proxy_test.ObjectLoader();
      //var user = proxy.openObject("cn=test test,ou=people,dc=example,dc=net");
      //console.log("now:"  + user.getTelephoneNumber());
    }
  }
});
