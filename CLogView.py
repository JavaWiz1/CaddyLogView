import argparse
import json
import operator
import os
import pathlib
import re
import sys
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Tuple
from io import TextIOWrapper

DEFAULT_LOGFORMAT = '{ts} | {level:8} | {duration:>5}ms | {status:>3} | {request.method:6} | {request.uri}'
DUMMY_LOGFORMAT   = '"{ts} | {status:>3} | {request.uri}"'
DESCRIPTION = '''
A simple Caddy logfile viewer
-----------------------------------------------------------------------
Simplifies the viewing of standard Caddy formatted log files, with
some color coding capabilities for log level and response status codes.
'''
EPILOG = f'''
* Defaults:
    log-format : {DEFAULT_LOGFORMAT}

* Environment Overrides.
  A .env may be supplied to override default values.
    ex (.env):
        log-format = {DUMMY_LOGFORMAT}
        colorize = True
        non-access = True

* Paging 
  Can be accomplished by piping into less (with -r parameter)
    ex:   python caddy_logview.py caddy.log | less -r
'''
# Style Shortcuts
class STYLE:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
'''Ansi console style constants (BOLD/UNDERLINE)'''

# Color Shortcuts
class COLOR:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE   = "\033[34m"
    BRIGHT_CYAN = "\033[96m"
    BG_RED = "\033[41m"
'''Ansi console color constants'''

class LogProcessor():
    '''
    Process a Caddy formatted logfile and output to the console (stdout)
    '''
    def __init__(self, log_filename: str, format: str, colorize: bool = False, show_non_accesslog_lines: bool = False):
        self._logfile = pathlib.Path(log_filename)
        if not self._logfile.exists():
            raise FileNotFoundError(f'{log_filename} does NOT exist.')
        if not self._logfile.is_file():
            raise FileNotFoundError(f'{log_filename} is not a valid file.')

        self._format = format
        self._hilite = colorize
        self._show_non_accesslog_lines = show_non_accesslog_lines

        self.logline_meta_definitions = re.findall(r"\{(.*?)\}", format)

    # -- Public Methods --------------------------------------------------------------------------------------
    def process_log(self):
        '''
        Output ALL log lines to stdout
        '''
        buffer = self._logfile.read_text().splitlines()
        lineno = 0
        print(f'~ {len(buffer)} lines loaded.')
        for line in buffer:
            lineno += 1
            json_line = json.loads(line,object_hook=lambda d: SimpleNamespace(**d))
            if not self._show_non_accesslog_lines and 'request' not in vars(json_line).keys():
                continue

            out_line = self._translate_log_line(json_line)
            print(out_line)

    def tail_log(self):
        '''Tail log file, include last 10 lines.'''
        # print(f'``Last 10 lines...')
        last10 = self._get_last_n_lines()
        for line in last10:
            json_line = json.loads(line,object_hook=lambda d: SimpleNamespace(**d))
            out_line = self._translate_log_line(json_line)
            print(out_line)

        # Begin tailing the file...
        for line in self._tail_file():
            json_line = json.loads(line,object_hook=lambda d: SimpleNamespace(**d))
            out_line = self._translate_log_line(json_line)
            print(out_line, flush=True)


    def list_caddy_log_fields(self):
        '''Print log line caddy fields that can be used in log format.'''
        caddy_fields = self._get_logline_keys()
        for field in caddy_fields:
            print(field)

    # -- Private Methods --------------------------------------------------------------------------------------
    def _get_last_n_lines(self, n:int=10, buffer_size:int=8192) -> list:
        """
        Reads the last N lines of a file efficiently by working backwards from the end.
        """
        if n <= 0:
            return []
        try:
            with open(self._logfile, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                
                lines_found = []
                buffer = bytearray()
                pointer = file_size
                
                # Read backwards in blocks until we have enough lines
                while pointer > 0 and len(lines_found) <= n:
                    # Determine how much to read
                    read_size = min(buffer_size, pointer)
                    pointer -= read_size
                    
                    f.seek(pointer)
                    chunk = f.read(read_size)
                    buffer = chunk + buffer
                    
                    # Split buffer into lines
                    lines_found = buffer.split(b'\n')
                    
                    # If we haven't reached the beginning of the file, 
                    # the first partial element of lines_found might be incomplete. 
                    # We leave it in the buffer for the next backward read loop.
                    if pointer > 0:
                        buffer = lines_found[0]
                        lines_found = lines_found[1:]
                
                # Decode the exact number of requested lines from bytes to string
                result = [line.decode('utf-8', errors='ignore') + '\n' for line in lines_found[-n:]]
                # Clean up trailing newline artifacts if the last line was empty
                if result and result[-1] == '\n' and len(lines_found) > n:
                    result.pop()
                    
                return result

        except FileNotFoundError:
            print(f"Error: The file '{self._logfile}' does not exist.")
            return []

    def _tail_file(self, read_from_end=True):
        """
        Yields new lines from a file as they are written, mimicking 'tail -f'.
        
        :param filename: Path to the log file.
        :param read_from_end: If True, skips old logs and starts reading from the current end.
                            If False, reads the entire file from the beginning first.
        """
        def open_file_safely(path, read_end):
            try:
                print('~ open file safely')
                f = open(path, 'r', encoding='utf-8', errors='ignore')
                # Track the unique OS Inode identifier of the file (falls back to path metadata on Windows)
                stat = os.stat(path)
                inode = stat.st_ino if hasattr(stat, 'st_ino') else stat.st_ctime
                
                if read_end:
                    f.seek(0, os.SEEK_END)
                return f, inode
            except FileNotFoundError:
                return None, None

        # Initial file capture
        f_handle: TextIOWrapper|None
        current_inode: int|float|None
        f_handle, current_inode = open_file_safely(self._logfile, read_from_end)
        # If the file doesn't exist yet, wait until it is created
        while f_handle is None:
            print(f"Waiting for log file '{self._logfile}' to be created...")
            time.sleep(2)
            f_handle, current_inode = open_file_safely(self._logfile, read_from_end)

        try:
            while True:
                current_position = f_handle.tell()
                line = f_handle.readline()
                
                if not line:
                    # No data read. Check if log rotation or truncation just happened.
                    try:
                        stat = os.stat(self._logfile)
                        new_inode = stat.st_ino if hasattr(stat, 'st_ino') else stat.st_ctime
                        
                        # File was truncated (size is smaller than our pointer)
                        if stat.st_size < current_position:
                            print("\n[Log rotation detected: File was truncated. Resetting pointer...]")
                            f_handle.seek(0)
                            continue
                            
                        # File was renamed/replaced (Inode changed)
                        if new_inode != current_inode:
                            print("\n[Log rotation detected: File was replaced. Re-opening...]")
                            f_handle.close()
                            f_handle, current_inode = open_file_safely(self._logfile, read_end=False)
                            continue
                            
                    except FileNotFoundError:
                        # The file might be temporarily missing during the rotation dance
                        time.sleep(0.5)
                        continue

                    # No data and no rotation? Just rest before checking for lines again.
                    time.sleep(0.1)
                    continue
                
                # If the line isn't fully committed to disk yet, rollback and wait
                if not line.endswith('\n'):
                    # print('~ wait for EOL')
                    f_handle.seek(current_position)
                    time.sleep(0.1)
                    continue
                # print(f'~ yield the line')
                yield line

        except KeyboardInterrupt:
            print("\ntail stopped.")
        finally:
            if f_handle:
                f_handle.close()

    def _translate_log_line(self, json_logline: dict) -> str:
        out_line = self._format
        line_level = ''
        for field_def in self.logline_meta_definitions:
            field_name, field_fmt = self._resolve_meta_definition(field_def)
            the_field = operator.attrgetter(field_name)
            try:
                field_value = the_field(json_logline)
                if field_name == 'level':
                    line_level = field_value
            except AttributeError:
                field_value = '' if field_name != 'request.uri' else json_logline.msg
            resolved_value = self._translate_field(field_name, field_fmt, field_value)
            out_line = out_line.replace('{'+field_def+'}', str(resolved_value))

        if self._hilite:
            # Color output line based on log level
            if line_level in ["warning","warn"]:
                out_line = out_line.replace(STYLE.RESET, COLOR.YELLOW)
                out_line = f'{COLOR.YELLOW}{out_line}{STYLE.RESET}'
            elif line_level in ["error","exception","critical"]:
                out_line = out_line.replace(STYLE.RESET, COLOR.RED)
                out_line = f'{COLOR.RED}{out_line}{STYLE.RESET}'
            elif line_level in ["trace", "debug"]:
                out_line = out_line.replace(STYLE.RESET, COLOR.BLUE)
                out_line = f'{COLOR.BLUE}{out_line}{STYLE.RESET}'
        
        return out_line
    
    def _resolve_meta_definition(self, meta_field: str) -> Tuple[str, str]:
        token = meta_field.split(":")
        var_name = token[0]
        var_fmt = "" if len(token) == 1 else token[1]
        return var_name, var_fmt

    def _translate_field(self, meta_field: str, meta_fmt:str, value: Any) -> Any:
        new_val = value
        # Translate field if needed
        if meta_field == 'ts' and isinstance(value,float):
            new_val = datetime.fromtimestamp(value).strftime("%m/%d/%Y %H:%M:%S")
        elif meta_field == 'duration':
            if isinstance(value, float):
                new_val = round(float(value)*1000)
        elif meta_field == 'level':
            new_val = new_val.upper()

        if meta_fmt:
            new_val = f'{new_val:{meta_fmt}}'

        # Apply color/format if needed
        if meta_field == 'level':
            if new_val in ['ERROR','EXCEPTION','CRITICAL']:
                new_val = f'{COLOR.RED}{new_val}{STYLE.RESET}'
            elif new_val in ['WARN', 'WARNING']:
                new_val = f'{COLOR.YELLOW}{new_val}{STYLE.RESET}'
            elif new_val in ['TRACE', 'DEBUG']:
                new_val = f'{COLOR.BLUE}{new_val}{STYLE.RESET}'
        elif meta_field == 'status':
            if isinstance(value, int):
                if value >= 500:
                    new_val = f'{COLOR.RED}{value}{STYLE.RESET}'
                elif value >= 400:
                    new_val = f'{COLOR.YELLOW}{value}{STYLE.RESET}'
                else:
                    new_val = f'{COLOR.GREEN}{value}{STYLE.RESET}'

        return new_val
    
    def _get_logline_keys(self) -> list:
        json_line: dict = {}
        with open(self._logfile, 'r') as file:
            json_line = json.loads(file.readline().strip())
            while 'request' not in json_line:
                json_line = json.loads(file.readline().strip())
        return self._build_caddy_field_list(json_line)

    def _build_caddy_field_list(self, dict_block: dict, current_path:str="", key_list:list|None=None):
        if key_list is None:
            key_list = []
        for key, value in dict_block.items():
            # Build the path string
            new_path = f"{current_path}.{key}" if current_path else key
            key_list.append(new_path)
            
            # If the value is a dictionary, keep digging
            if isinstance(value, dict):
                self._build_caddy_field_list(value, new_path, key_list)

        return key_list
        
# -- Module level functions -----------------------------------------------------------------------------------
def load_native_env(env_path=".env"):
    """Reads a .env file and loads values into os.environ natively."""
    path = pathlib.Path(env_path)
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Split by the first '=' character
            if "=" in line:
                key, value = line.split("=", 1)
                # Strip spaces and optional quotes from keys/values
                key = key.strip()
                value = value.strip().strip("'\"")
                # Set the environment variable
                os.environ[key] = value

def main() -> int:
    load_native_env()
    default_format      = os.environ.get('log-format', DEFAULT_LOGFORMAT)
    colorize_line       = os.environ.get('colorize', False)
    non_access_enabled  = os.environ.get('non-access', False)

    parser = argparse.ArgumentParser(description=DESCRIPTION, 
                                     epilog=EPILOG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('logfile', nargs=1)
    parser.add_argument('-fmt', '--log-format', default=default_format, 
                        help='Log line format.  Based on caddy fields (see --list parameter).')
    parser.add_argument('-f', '--follow', action='store_true', default=False,
                        help='Follow file output')
    parser.add_argument('-l', '--list', action='store_true', default=False, 
                        help='List all log line fields, then exit.')
    parser.add_argument('-c', '--colorize', action='store_true', default=colorize_line, 
                        help='Hilite line based on log level.')
    parser.add_argument('-na','--non-access',action='store_true',default=non_access_enabled,  
                        help='Display non-access log entries.')
    args = parser.parse_args()
    print(f'File:   {args.logfile[0]}')
    print(f'format: {args.log_format}')
    print('`')
    lp = LogProcessor(args.logfile[0], args.log_format, args.colorize, args.non_access)
    if args.list:
        lp.list_caddy_log_fields()
        return 0
    rc = 0
    try:
        if args.follow:
            lp.tail_log()
        else:
            lp.process_log()
    except (BrokenPipeError, OSError, KeyboardInterrupt):
        print('Processing interrupted.')
        rc = 1
    return rc

if __name__ == "__main__":
    sys.exit(main())
