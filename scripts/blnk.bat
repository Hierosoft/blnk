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

REM Check return code
if %code% neq 0 (
    REM BAD Count lines in err.log
    for /f %%A in ('find /v /c "" ^< "%logsDir%\err.log"') do set "err_line_count=%%A"
    echo err_line_count=%err_line_count%
    type "%logsDir%\err.log" 1>&2
    echo Showing a GUI dialog box... 1>&2
    if %err_line_count% gtr 0 (
        REM Show error message box
        REM mshta vbscript:Execute("msgbox ""See %logsDir%\out.log (usually err.log, but that appears to be blank)"":close")
        type "%logsDir%\err.log" 1>&2
    ) else (
        set "msg=Blnk had an unrecorded error. See %logsDir%\out.log for information about the last run."
        REM mshta vbscript:Execute("msgbox ""%msg%"":close")
    )
    exit /b %code%
) else (
    REM OK Count lines in err.log
    for /f %%A in ('find /v /c "" ^< "%logsDir%\err.log"') do set "err_line_count=%%A"
    echo err_line_count=%err_line_count%
    if %err_line_count% gtr 0 (
        type "%logsDir%\err.log" 1>&2
    )
)

endlocal
