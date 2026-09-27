# CaddyLogView
A python filter to view Caddy formatted log files. 

Simplifies the viewing of standard Caddy formtted log files, with
some minor color coding capabilities to enhance viewing.

Syntax:   

    python CLogView.py [-h] [-fmt LOG_FORMAT] [-f] [-l] [-c] [-na] logfile

To get paging capabilities, you can combine with less -r
    
    python CLogView.py caddy.log | less -r

## Parameter Notes:
| Parameter | Note |
| --------- | ---- |
| -c, --colorize | Will hi-lite logline based on log level for that line (even if level is not displayed).<br> * debug - <span style="color:blue">BLUE</span><br> * warn  - <span style="color:yellow">YELLOW</span><br> * error - <span style="color:red">RED</span> |
| -fmt           | Log line format string.  (See env.tempate for example) |
| -l, --list     | Parameter will list all caddy fields that can be displayed and configured for log line (--fmt). |
| -f, --follow   | Similar to tail.  Will display last 10 lines, then tail the file |
| -na, --non-access | Will ONLY display lines generated via logger 'http.log.access.*' |

## Notes:
* An **'.env'** file can be set to customize behavior.  (See env.template)
* Command-line parameters over-ride defaults and .env settings if provided.
