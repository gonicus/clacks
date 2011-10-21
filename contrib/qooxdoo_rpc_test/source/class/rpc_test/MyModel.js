qx.Class.define("rpc_test.MyModel",
{
  extend : qx.ui.table.model.Remote,
  members :
  {


    _loadRowCount : function()
    {
        var rpc = new qx.io.remote.Rpc("https://amqp.intranet.gonicus.de/rpc", "GOsa JSON-RPC service");
        rpc.setTimeout(10000);
        that = this;
        res = rpc.callAsync(function(result){
                that._onRowCountLoaded(result.length);
            },"search", "dc=gonicus,dc=de", 2, {'type': 'GenericUser'}, ['sn']);
    },
 
    // overloaded - called whenever the table requests new data
    _loadRowData : function(firstRow, lastRow)
    {
        var rpc = new qx.io.remote.Rpc("https://amqp.intranet.gonicus.de/rpc", "GOsa JSON-RPC service");
        rpc.setTimeout(10000);
        res = rpc.callAsync(function(result){
                that._onRowDataLoaded(result);
            },"search", "dc=gonicus,dc=de", 2, {'type': 'GenericUser'}, ['sn', 'givenName','uid'], firstRow,lastRow);
    }
  }  
});
