@echo off
setlocal

REM Create directories
set "logsDir=%LOCALAPPDATA%\blnk\logs"
if not exist "%logsDir%" mkdir "%logsDir%"
echo Using "%logsDir%"
REM Set Exec if not already set
if "%Exec%"=="" (
    set "Exec=%USERPROFILE%\git\blnk\blnk\__init__.py"
)

REM Echo logsDir
echo logsDir=%logsDir% 1>&2

REM Create out.log
echo Output: > "%logsDir%\out.log"

REM Append date to out.log
date /T >> "%logsDir%\out.log"

REM Run python3 with Exec
python "%Exec%" --non-interactive %* >> "%logsDir%\out.log" 2> "%logsDir%\err.log"
set "code=%errorlevel%"

REM Append newline to out.log
echo. >> "%logsDir%\out.log"

REM Output out.log
type "%logsDir%\out.log"
REM echo code is %code%
REM Check return code
set err_line_count=0
REM ^ Ensure it is never blank, or neq 0 will always run
REM   "0 was unexpected" since nested "if" will resolve to:
REM   "if  gtr 0 ("
FOR /F %%i IN ('TYPE "%logsDir%\err.log" ^| FIND /C /V ""') DO SET err_line_count=%%i
if %code% neq 0 (
    echo "[blnk.bat] error nonzero return code %code%
    REM BAD Count lines in err.log
    REM for /f %%A in ('find /v /c "" ^< "%logsDir%\err.log"') do set "err_line_count=%%A"
    
    REM NOTE: Using %% is only necessary in a batch file. To test it live, use only % not %%
    REM   (See <https://stackoverflow.com/questions/9311562/a-was-unexpected-at-this-time>)
    echo err_line_count=%err_line_count%
    type "%logsDir%\err.log" 1>&2
    echo Showing a GUI dialog box... 1>&2
    if %err_line_count% gtr 0 (
        REM Show error message box
        REM mshta vbscript:Execute("msgbox ""See %logsDir%\out.log (usually err.log, but that appears to be blank)"":close")
        notepad "%logsDir%\err.log"
        type "%logsDir%\err.log" 1>&2
    ) else (
        set "msg=Blnk had an unrecorded error. See %logsDir%\out.log for information about the last run."
        REM mshta vbscript:Execute("msgbox ""%msg%"":close")
        echo. >> "%logsDir%\out.log"
        echo "[blnk.bat] code %code%" >> "%logsDir%\out.log"
        echo "[blnk.bat] err_line_count %err_line_count%" >> "%logsDir%\out.log"
        echo "[blnk.bat] %msg%" >> "%logsDir%\out.log"
        notepad "%logsDir%\out.log"
    )
    exit /b %code%
) else (
    echo "[blnk.bat] OK return code %code%"
    REM OK Count lines in err.log
    REM for /f %%A in ('find /v /c "" ^< "%logsDir%\err.log"') do set "err_line_count=%%A"
    REM for /f %%A in ('TYPE "%logsDir%\err.log" ^| FIND /C /V ""') do set "err_line_count=%%A"
    REM echo err_line_count=%err_line_count%
    if %err_line_count% gtr 0 (
        type "%logsDir%\err.log" 1>&2
    )
)

endlocal
