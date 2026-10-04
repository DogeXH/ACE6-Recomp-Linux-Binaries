#!/usr/bin/env python3
"""Launch the tested native build and restore this launch's GPU policy."""
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    game = Path(__file__).resolve().parent / 'ac6recomp'
    runtime_setting = os.environ.get('AC6_GLIBC_RUNTIME', '')
    runtime = Path(runtime_setting).expanduser().resolve() if runtime_setting else None
    env = dict(os.environ)
    for key in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'ENABLE_VULKAN_RENDERDOC_CAPTURE',
                'AC6_NR2_RENDERDOC_CAPTURE', 'ENABLE_VK_LAYER_VALVE_steam_overlay_1',
                'ENABLE_VK_LAYER_VALVE_steam_fossilize_1',
                'SDL_GAMECONTROLLER_IGNORE_DEVICES_EXCEPT',
                'SDL_GAMECONTROLLER_IGNORE_DEVICES',
                'SDL_GAMECONTROLLER_ALLOW_STEAM_VIRTUAL_GAMEPAD',
                'AC6_ALLOW_DEBUG_ATTACH', 'AC6_TIMING_TRACE', 'AC6_TRACE_SAVE_IO'):
        env.pop(key, None)
    env.setdefault('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
    env.update(SDL_AUDIODRIVER='pulseaudio',
               PULSE_SERVER='unix:' + env['XDG_RUNTIME_DIR'] + '/pulse/native',
               DISABLE_VULKAN_RENDERDOC_CAPTURE_1_36='1',
               VK_LOADER_LAYERS_DISABLE='VK_LAYER_RENDERDOC_Capture',
               AC6_NR2_PERF_LOG='0', AC6_NR2_FRAME_STATS='0')
    library_path = str(runtime) + ':/usr/lib' if runtime else '/usr/lib'
    mesa = game.parent / 'mesa-26.1.7'
    if env.get('AC6_USE_PRIVATE_MESA', '1') != '0' and (mesa/'radeon.json').is_file():
        library_path = (str(runtime) + ':' if runtime else '') + str(mesa/'lib') + ':/usr/lib'
        if runtime is None:
            env['LD_LIBRARY_PATH'] = library_path
        env['VK_DRIVER_FILES'] = str(mesa/'radeon.json')
        env['VK_ICD_FILENAMES'] = str(mesa/'radeon.json')
        env['MESA_SHADER_CACHE_DIR'] = str(mesa/'cache')
    lock = open(Path(env['XDG_RUNTIME_DIR']) / 'ac6-native-launch.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('AC6 is already running.', file=sys.stderr)
        return 1
    dpm = Path('/sys/class/drm/card0/device/power_dpm_force_performance_level')
    helper = '/usr/bin/steamos-polkit-helpers/steamos-priv-write'
    tune = env.get('AC6_DECK_TUNE', '1') == '1'
    previous = None
    changed = False
    child = None
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    def write_gpu(value):
        try:
            return subprocess.run([helper, str(dpm), value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    try:
        if tune and env.get('AC6_NO_GPU_PIN', '0') != '1' and dpm.exists():
            previous = dpm.read_text().strip()
            if previous != 'high':
                changed = write_gpu('high')
        command = [str(game), *sys.argv[1:]]
        if runtime is not None:
            command = [str(runtime/'ld-linux-x86-64.so.2'),
                       '--library-path', library_path, *command]
        child = subprocess.Popen(command, cwd=game.parent, env=env)
        next_sweep = 0
        while child.poll() is None and not stopping:
            now = time.monotonic()
            if tune and now >= next_sweep:
                for thread in Path(f'/proc/{child.pid}/task').glob('*'):
                    try:
                        name = (thread/'comm').read_text().strip()
                        if name == 'Audio Worker':
                            cores = {7}
                        elif name in ('XMA Decoder', 'AC6 XAudioDSP'):
                            cores = {6}
                        elif env.get('AC6_ISOLATE_GPU_COMMAND', '1') != '0':
                            cores = {0} if name.startswith('GPU Commands') else set(range(2,6))
                        else:
                            cores = set(range(6))
                        os.sched_setaffinity(int(thread.name), cores)
                    except OSError:
                        pass
                next_sweep = now + 10
            time.sleep(0.5)
        if child.poll() is None:
            # Close this launch's own windows; never send gameplay inputs.
            try:
                windows = subprocess.run(['xdotool', 'search', '--pid', str(child.pid)],
                    env=env, capture_output=True, text=True, timeout=3)
                for window in windows.stdout.splitlines():
                    subprocess.run(['xdotool', 'windowquit', window], env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                child.wait(timeout=8)
            except (OSError, subprocess.TimeoutExpired):
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
        return max(0, child.returncode) if child.returncode == 0 else 1
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if changed:
            try:
                if dpm.read_text().strip() == 'high':
                    write_gpu(previous)
            except OSError:
                pass


if __name__ == '__main__':
    sys.exit(main())
