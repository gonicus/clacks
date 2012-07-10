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

      proxy_test.ObjectFactory.openObject(function(object){

          // Set values without callback
          object.setTelephoneNumber(['123', 'asdfasdf']);
          object.setUid("test");
          object.setDepartmentNumber("asdf");

          // Commit changes without callback
          object.commit();

          // object.commit(function(){...}, this)     <--  with callback

          // List object attributes
          object.get_attributes(function(result){
            console.log(result);
          }, this);
          
          // Change the users password
          object.changePassword(function(result){
            console.log("Password changed");
          }, this, "tester123");

        }, this, "cn=test test,ou=people,dc=example,dc=net");
    }
  }
});