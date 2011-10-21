Logging
=======

Logging is handled by the default python logging module. To configure
logging for GOsa, you can add the following infomration to your main
GOsa configuration file, or - at your choice - create a new file for
logging inside the config.d directory.

Here's an example:

	[loggers]
	keys=root,gosa
	
	[handlers]
	keys=syslog,console,file
	
	[formatters]
	keys=syslog,console
	
	
	[logger_root]
	level=CRITICAL
	handlers=console
	
	[logger_gosa]
	level=INFO
	handlers=console
	qualname=gosa
	propagate=0
	
	[handler_console]
	class=StreamHandler
	formatter=console
	args=(sys.stderr,)
	
	[handler_syslog]
	class=logging.handlers.SysLogHandler
	formatter=syslog
	args=('/dev/log',)
	
	[handler_file]
	class=logging.handlers.TimedRotatingFileHandler
	formatter=syslog
	args=('/var/log/gosa/agent.log', 'w0', 1, 4)
	
	[formatter_syslog]
	format=%(levelname)s: %(module)s - %(message)s
	datefmt=
	class=logging.Formatter
	
	[formatter_console]
	format=%(asctime)s %(levelname)s: %(module)s - %(message)s
	datefmt=
	class=logging.Formatter
	
