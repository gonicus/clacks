qx.Class.define("proxy_test.ui.LoginDialog",
{
  extend : qx.ui.window.Window,

  construct : function()
  {
    this.base(arguments);

    /* Container layout */

    var layout = new qx.ui.layout.Grid(9, 5);
    layout.setColumnAlign(0, "right", "top");
    layout.setColumnAlign(2, "right", "top");

    this.setCaption(this.tr("Login"));
    this.setLayout(layout);
    this.setModal(true);
    this.setShowClose(false);
    this.setAllowMinimize(false);
    this.setAllowMaximize(false);
    this.setShowMinimize(false);
    this.setShowMaximize(false);

    /* Try to receive currently loggedin user */

    this.setWidth(220);

    /* Labels */

    var labels = [ this.tr("Name"), this.tr("Password") ];

    for (var i=0; i<labels.length; i++)
    {
      this.add(new qx.ui.basic.Label(labels[i]).set(
      {
        allowShrinkX : false,
        paddingTop   : 3
      }),
      {
        row    : i,
        column : 0
      });
    }

    this.__username = new qx.ui.form.TextField();
    this.__username.activate();
    this.__password = new qx.ui.form.PasswordField();

    this.add(this.__username.set(
    {
      allowGrowX   : true,
      allowShrinkX : true,
      width        : 200,
      paddingTop   : 3
    }),
    {
      row    : 0,
      column : 1
    });

    this.add(this.__password.set(
    {
      allowGrowX   : true,
      allowShrinkX : true,
      width        : 200,
      paddingTop   : 3
    }),
    {
      row    : 1,
      column : 1
    });

    this.__info = new qx.ui.basic.Label().set(
    {
      rich   : true,
      alignX : "left"
    });
    this.add(this.__info,
    {
      row     : 3,
      column  : 0,
      colSpan : 2
    });

    /* Button */
    var login = new qx.ui.form.Button(this.tr("Login"));
    login.setAllowStretchX(false);

    this.add(login,
    {
      row    : 5,
      column : 0
    });

    login.addListener("click", function(){
        var rpc = proxy_test.io.Rpc.getInstance();
        var that = this;
        rpc.callAsync(function(result, error){
            if(!result){
              that.__info.setValue(this.tr("Invalid login ..."));
            }else{
              that.close();
              that.fireEvent("login");
            }
          }, "login", this.__username.getValue(), this.__password.getValue());
      }, this);
  },

  events: {
    "login": "qx.event.type.Event"
  }
});

