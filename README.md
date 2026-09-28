# CaddyLogView
A python filter to view Caddy formatted log files. 

Simplifies the viewing of standard Caddy formtted log files, with
some minor color coding capabilities to enhance viewing.

Transform this:
```
{"level":"info","ts":1790435959.9907265,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0x4000558b60"}
{"level":"warn","ts":1790435959.990835,"logger":"http","msg":"automatic HTTPS is completely disabled for server","server_name":"srv0"}
{"level":"info","ts":1790435959.9995232,"logger":"tls","msg":"cleaning storage unit","description":"FileStorage:/var/lib/caddy/.local/share/caddy"}
{"level":"info","ts":1790435959.999831,"logger":"tls","msg":"finished cleaning storage units"}
{"level":"info","ts":1790435959.999846,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
{"level":"info","ts":1790435962.5733893,"logger":"http.log.access.log4","msg":"handled request","request":{"remote_ip":"192.168.1.xxx","remote_port":"60866","proto":"HTTP/1.1","method":"GET","host":"raspiweb3a.mynet","uri":"/devices/switch/BlinkPlug","headers":{"Accept":["*/*"],"Accept-Encoding":["gzip, deflate, br"],"Connection":["keep-alive"],"User-Agent":["HomeAssistant/2026.9.3 httpx/0.28.1 Python/3.14"],"Content-Type":["application/json"]}},"user_id":"","duration":0.454392305,"size":30,"status":200,"resp_headers":{"Server":["Caddy","uvicorn"],"Access-Control-Allow-Origin":["*"],"Access-Control-Allow-Methods":["GET, POST, PUT, DELETE, OPTIONS"],"Date":["Sat, 26 Sep 2026 15:19:21 GMT"],"Content-Length":["30"],"Content-Type":["application/json"]}}
{"level":"info","ts":1790435966.1257443,"logger":"http.log.access.log4","msg":"handled request","request":{"remote_ip":"192.168.1.xxx","remote_port":"60866","proto":"HTTP/1.1","method":"GET","host":"raspiweb3a.mynet","uri":"/devices/switch/Samsung","headers":{"Content-Type":["application/json"],"Accept":["*/*"],"Accept-Encoding":["gzip, deflate, br"],"Connection":["keep-alive"],"User-Agent":["HomeAssistant/2026.9.3 httpx/0.28.1 Python/3.14"]}},"user_id":"","duration":2.021203544,"size":31,"status":200,"resp_headers":{"Date":["Sat, 26 Sep 2026 15:19:23 GMT"],"Content-Length":["31"],"Server":["Caddy","uvicorn"],"Access-Control-Allow-Origin":["*"],"Access-Control-Allow-Methods":["GET, POST, PUT, DELETE, OPTIONS"],"Content-Type":["application/json"]}}
```
into this:
```log
09/26/2026 11:19:19 | INFO     |      ms |     |        | started background certificate maintenance
09/26/2026 11:19:19 | WARN     |      ms |     |        | automatic HTTPS is completely disabled for server
09/26/2026 11:19:19 | INFO     |      ms |     |        | cleaning storage unit
09/26/2026 11:19:19 | INFO     |      ms |     |        | finished cleaning storage units
09/26/2026 11:19:19 | INFO     |      ms |     |        | server running
09/26/2026 11:19:22 | INFO     |   454ms | 200 | GET    | raspiweb3a.mynet/devices/switch/BlinkPlug
09/26/2026 11:19:26 | INFO     |  2021ms | 200 | GET    | raspiweb3a.mynet/devices/switch/Samsung
```

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
