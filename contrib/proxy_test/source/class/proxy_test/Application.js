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

      // Create a button
      var proxy = new proxy_test.ObjectLoader();
      var user = proxy.openObject("cn=test test,ou=people,dc=example,dc=net");
      user.setTelephoneNumber([1234]);
      user.commit();
      
      var user2 = proxy.openObject("ou=people,dc=example,dc=net", "User");
      user2.setSn("test123");
      user2.setGivenName("test123");
      user2.setUid("test123");
      user2.commit();

    }
  }
});
