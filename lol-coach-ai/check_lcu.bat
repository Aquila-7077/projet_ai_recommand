@echo off
setlocal enabledelayedexpansion

REM Chemins communs pour lockfile
set "p1=%LOCALAPPDATA%\Riot Games\League of Legends\lockfile"
set "p2=%ProgramFiles%\Riot Games\League of Legends\lockfile"
set "p3=%ProgramFiles(x86)%\Riot Games\League of Legends\lockfile"
set "p4=%CD%\lockfile"

echo Checking possible lockfile locations...
for %%P in ("%p1%" "%p2%" "%p3%" "%p4%") do (
  if exist "%%~P" (
    echo ===============================================
    echo FOUND: %%~P
    echo ---------- content ----------
    type "%%~P"
    echo --------------------------------
    set "FOUND=1"
  ) else (
    echo Not found: %%~P
  )
)

if defined FOUND (
  echo.
  echo If a lockfile line was printed above, it should look like:
  echo name:pid:port:password:protocol
  echo.
  echo To test the champ-select endpoint with curl, run the command below, replacing PORT and PASSWORD.
  echo Example:
  echo curl -k -u riot:THEPASSWORD "https://127.0.0.1:PORT/lol-champ-select/v1/session" --max-time 5
) else (
  echo.
  echo No lockfile found in common locations.
  echo If League is installed to a custom path, set the environment variable LCU_LOCKFILE before running the server.
  echo Example (cmd session only):
  echo set LCU_LOCKFILE=C:\Chemin\Vers\lockfile
)

endlocal
pause