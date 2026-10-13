"""Register the daily no-LLM discovery (and optionally the full CLI run) with the OS scheduler.

Windows: Task Scheduler (only while the user is logged on, StartWhenAvailable, 6 h limit).
macOS: a LaunchAgent in ~/Library/LaunchAgents (missed runs fire once after wake).
"""
import os
import plistlib
import subprocess
import sys
from pathlib import Path

from . import paths

TASKS = {'discover': 'GetMeAJob Discover', 'daily': 'GetMeAJob Daily'}
LABEL = 'com.criptochairo.getmeajob.{}'


def python_exe(windowless=True):
    exe = Path(sys.executable)
    if windowless and os.name == 'nt' and (exe.parent / 'pythonw.exe').exists():
        return str(exe.parent / 'pythonw.exe')
    return str(exe)


def args_for(kind):
    return ['-m', 'gmaj', 'discover'] if kind == 'discover' else ['-m', 'gmaj', 'run-daily']


def plist_path(kind):
    return Path.home() / 'Library/LaunchAgents' / f'{LABEL.format(kind)}.plist'


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def install(kind='discover', at='08:30', runner=subprocess.run):
    hour, minute = (int(x) for x in at.split(':'))
    logs = paths.user('logs')
    logs.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        argument = ' '.join(args_for(kind))
        script = (
            f"$a = New-ScheduledTaskAction -Execute {ps_quote(python_exe())} -Argument {ps_quote(argument)} -WorkingDirectory {ps_quote(paths.ROOT)};"
            f"$t = New-ScheduledTaskTrigger -Daily -At {ps_quote(f'{hour:02d}:{minute:02d}')};"
            "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 6) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;"
            "$p = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive;"
            f"Register-ScheduledTask -TaskName {ps_quote(TASKS[kind])} -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null"
        )
        result = runner(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, text=True)
        return result.returncode == 0, (result.stderr or '').strip() or f'Tarea "{TASKS[kind]}" registrada a las {at}'
    if sys.platform == 'darwin':
        path = plist_path(kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        label = LABEL.format(kind)
        with open(path, 'wb') as stream:
            plistlib.dump({
                'Label': label, 'ProgramArguments': [python_exe(False), *args_for(kind)],
                'WorkingDirectory': str(paths.ROOT), 'StartCalendarInterval': {'Hour': hour, 'Minute': minute},
                'StandardOutPath': str(logs / f'{kind}.out.log'), 'StandardErrorPath': str(logs / f'{kind}.err.log'),
                'EnvironmentVariables': {'PYTHONIOENCODING': 'utf-8', 'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            }, stream)
        uid = os.getuid()
        runner(['launchctl', 'bootout', f'gui/{uid}', str(path)], capture_output=True)
        result = runner(['launchctl', 'bootstrap', f'gui/{uid}', str(path)], capture_output=True, text=True)
        return result.returncode == 0, (result.stderr or '').strip() or f'LaunchAgent {label} cargado a las {at}'
    return False, 'Sistema no soportado para programar tareas (usa cron manualmente).'


def remove(kind='discover', runner=subprocess.run):
    if os.name == 'nt':
        result = runner(['schtasks', '/Delete', '/TN', TASKS[kind], '/F'], capture_output=True, text=True)
        return result.returncode == 0, (result.stdout or result.stderr or '').strip()
    if sys.platform == 'darwin':
        path = plist_path(kind)
        runner(['launchctl', 'bootout', f'gui/{os.getuid()}', str(path)], capture_output=True)
        path.unlink(missing_ok=True)
        return True, f'LaunchAgent {LABEL.format(kind)} eliminado'
    return False, 'Sistema no soportado'


def status(kind='discover', runner=subprocess.run):
    if os.name == 'nt':
        result = runner(['schtasks', '/Query', '/TN', TASKS[kind]], capture_output=True, text=True)
        return result.returncode == 0
    if sys.platform == 'darwin':
        return plist_path(kind).exists()
    return False
