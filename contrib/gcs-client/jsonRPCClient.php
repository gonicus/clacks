<?php
class jsonRPC {

    private $curlHandler = NULL;
    private $config;
    private $id;
    private $lastStats = array();
    private $lastAction = "none";

    public function __construct($url) 
    {
        $this->id = 0;

        // Init Curl handler
        $this->curlHandler = curl_init($url);

        // Set curl options
        curl_setopt($this->curlHandler, CURLOPT_URL , $url);
        curl_setopt($this->curlHandler, CURLOPT_USERPWD , "65717fe6-9e3e-11df-b010-5452005f1250:WyukwauWoid2");
        curl_setopt($this->curlHandler, CURLOPT_HTTPAUTH , CURLAUTH_ANYSAFE);
        curl_setopt($this->curlHandler, CURLOPT_POST , TRUE);
        curl_setopt($this->curlHandler, CURLOPT_RETURNTRANSFER , TRUE);
        curl_setopt($this->curlHandler, CURLOPT_HTTPHEADER , array('Content-Type: application/json'));
    }
        

    public function getHTTPstatusCode()
    {
        return((isset($this->lastStats['http_code']))? $this->lastStats['http_code'] : -1 );
    }

    public function get_error()
    {
        if($this->lastStats['http_code'] != 200){
            return($this->getHttpStatusCodeMessage($this->lastStats['http_code']));
        }else{
            return(curl_error($this->curlHandler));
        }
    }

    public function success()
    {
        return(curl_errno($this->curlHandler) == 0 && $this->lastStats['http_code'] == 200);
    }

    public function __destruct()
    {
        if($this->curlHandler){
             curl_close($this->curlHandler);
        }
    }

    public function __call($method,$params) 
    {
        // Check if handle is still valid!
        if(!$this->curlHandler && $this->lastAction != 'login'){
             $this->__login();
        }

        // Start request
        $response = $this->request($method,$params);
        return($response['result']);
    }

    
    private function request($method, $params)
    {
        // Set last action 
        $this->lastAction = $method;

        // Reset stats of last request.
        $this->lastStats = array();
   
        // Validate input  values
        if (!is_scalar($method))  trigger_error('jsonRPC::__call requires a scalar value as first parameter!');
        if (is_array($params)) {
            $params = array_values($params);
        } else {
            trigger_error('jsonRPC::__call requires an array value as second parameter!');
        }

        // prepares the request
        $this->id ++;
        $request = json_encode(array('method' => $method,'params' => $params,'id' => $this->id));

        // Set curl options
        curl_setopt($this->curlHandler, CURLOPT_POSTFIELDS , $request);
        $response = curl_exec($this->curlHandler);
        $response = json_decode($response,true);

        // Set current result stats.
        $this->lastStats = curl_getinfo($this->curlHandler);
    
        return($response);
    }
    

    public static function getHttpStatusCodeMessage($code)
    {
        $codes  = array(
                '100' =>  'Continue',
                '101' =>  'Switching Protocols',
                '102' =>  'Processing',
                '200' =>  'OK',
                '201' =>  'Created',
                '202' =>  'Accepted',
                '203' =>  'Non-Authoritative Information',
                '204' =>  'No Content',
                '205' =>  'Reset Content',
                '206' =>  'Partial Content',
                '207' =>  'Multi-Status',
                '300' =>  'Multiple Choice',
                '301' =>  'Moved Permanently',
                '302' =>  'Found',
                '303' =>  'See Other',
                '304' =>  'Not Modified',
                '305' =>  'Use Proxy',
                '306' =>  'reserved',
                '307' =>  'Temporary Redirect',
                '400' =>  'Bad Request',
                '401' =>  'Unauthorized',
                '402' =>  'Payment Required',
                '403' =>  'Forbidden',
                '404' =>  'Not Found',
                '405' =>  'Method Not Allowed',
                '406' =>  'Not Acceptable',
                '407' =>  'Proxy Authentication Required',
                '408' =>  'Request Time-out',
                '409' =>  'Conflict',
                '410' =>  'Gone',
                '411' =>  'Length Required',
                '412' =>  'Precondition Failed',
                '413' =>  'Request Entity Too Large',
                '414' =>  'Request-URI Too Long',
                '415' =>  'Unsupported Media Type',
                '416' =>  'Requested range not satisfiable',
                '417' =>  'Expectation Failed',
                '421' =>  'There are too many connections from your internet address',
                '422' =>  'Unprocessable Entity',
                '423' =>  'Locked',
                '424' =>  'Failed Dependency',
                '425' =>  'Unordered Collection',
                '426' =>  'Upgrade Required',
                '500' =>  'Internal Server Error',
                '501' =>  'Not Implemented',
                '502' =>  'Bad Gateway',
                '503' =>  'Service Unavailable',
                '504' =>  'Gateway Time-out',
                '505' =>  'HTTP Version not supported',
                '506' =>  'Variant Also Negotiates',
                '507' =>  'Insufficient Storage',
                '509' =>  'Bandwidth Limit Exceeded',
                '510' =>  'Not Extended');
        return((isset($codes[$code]))? $codes[$code] : sprintf(_("Unknown HTTP status code '%s'!"), $code));
    }
}
?>
