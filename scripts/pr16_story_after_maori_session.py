#!/usr/bin/env python3
"""固定runnerに通常ボタン/observe/quitだけを渡す新区間の開発セッション。"""
from __future__ import annotations
import json
from pathlib import Path
import queue
import subprocess
import threading
from pr16_story_after_maori import need, identity

ALLOWED_KEYS = {0, 1, 2, 8, 16, 32, 64, 128}


def key_command(key, frames):
    need(type(key) is int and key in ALLOWED_KEYS, 'single ordinary key only')
    need(type(frames) is int and 1 <= frames <= 600, 'bounded positive frame count')
    return f'key {key} {frames}\n'


class Session:
    def __init__(self, runtime, candidate, runner, seed, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=False)
        self.seed = seed
        self.save = self.folder / 'story.srm'
        self.save.write_bytes(seed)
        self.commands = (self.folder / 'commands.txt').open('w', encoding='utf-8')
        self.stdout = (self.folder / 'stdout.txt').open('w', encoding='utf-8')
        self.stderr = (self.folder / 'stderr.txt').open('wb')
        self.items = queue.Queue()
        self.records = []
        self.observations = []
        self.screen_records = []
        self.closed = False
        runtime = Path(runtime)
        args = [str(runtime / 'ld.so'), '--library-path', str(runtime / 'lib'), str(runner),
                str(candidate), str(self.save), 'continue-story', identity(seed)['sha256']]
        self.process = subprocess.Popen(args, cwd=self.folder, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.last = self._observation(0)

    def _read(self):
        try:
            for line in self.process.stdout:
                self.stdout.write(line)
                self.stdout.flush()
                self.items.put(json.loads(line))
        except Exception as error:
            self.items.put(error)
        finally:
            self.items.put(EOFError('runner output ended'))

    def _next(self):
        value = self.items.get(timeout=20)
        if isinstance(value, Exception):
            raise value
        self.records.append(value)
        return value

    def _observation(self, index):
        observation = None
        while True:
            value = self._next()
            if 'observe' in value:
                need(value['observe'] == index, 'exact observation order')
                observation = value
                self.observations.append(value)
            if 'screen' in value:
                need(value['screen'] == index and observation is not None, 'screen matched to observation')
                path = self.folder / f'screen-{index:04d}.ppm'
                need(identity(path.read_bytes())['sha256'] == value['sha256'], 'whole frame hash')
                self.screen_records.append(value)
                return observation

    def _send(self, text):
        need(not self.closed and self.process.poll() is None, 'live session')
        self.commands.write(text)
        self.commands.flush()
        self.process.stdin.write(text)
        self.process.stdin.flush()

    def step(self, *pairs):
        text = ''.join(key_command(key, frames) for key, frames in pairs)
        index = len(self.observations)
        self._send(text + f'observe {index}\n')
        self.last = self._observation(index)
        return self.last

    def quit(self):
        self._send('quit\n')
        self.process.stdin.close()
        ending = None
        while ending is None:
            value = self._next()
            if 'end' in value:
                ending = value
        code = self.process.wait(timeout=20)
        self.reader.join(timeout=2)
        self.closed = True
        self.commands.close()
        self.stdout.close()
        self.stderr.close()
        need(code == 0 and not (self.folder / 'stderr.txt').read_bytes(), 'clean native termination')
        result = dict(returncode=code, initial_save=identity(self.seed), final_save=identity(self.save.read_bytes()),
                      native_end=ending, observations=len(self.observations))
        (self.folder / 'execution.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        return result
