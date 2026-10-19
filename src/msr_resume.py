"""
Crash-safe collection primitives for the MSR 2027 pipeline.

Design rules, each learned from a way Colab actually fails:
  1. APPEND-ONLY JSONL, never rewrite-in-place. A crash mid-write loses at
     most the last partial line, not the whole file.
  2. ATOMIC writes for any file that must be rewritten (tmp + os.replace).
  3. FAILURES ARE RECORDED, so permanently-dead items are not retried forever.
  4. MIRRORED to Drive but WRITTEN to local disk, so a dropped Drive mount
     mid-run cannot corrupt the checkpoint.
  5. RESUME IS O(n), not O(n^2).
"""
from __future__ import annotations
import json, os, shutil, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


def atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'wb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


class ResumableCollector:
    """Append-only, crash-safe, resumable map over a list of string keys."""

    def __init__(self, name, local_dir='/content/msr_state', mirror_dir=None,
                 workers=12, flush_every=25, mirror_every=100, mirror_seconds=60, max_attempts=2):
        self.name = name
        self.local = Path(local_dir); self.local.mkdir(parents=True, exist_ok=True)
        self.mirror = Path(mirror_dir) if mirror_dir else None
        if self.mirror: self.mirror.mkdir(parents=True, exist_ok=True)
        self.workers, self.flush_every = workers, flush_every
        self.mirror_every, self.max_attempts = mirror_every, max_attempts
        self.mirror_seconds = mirror_seconds
        self._last_mirror = time.time()
        self.data_path = self.local/f'{name}.jsonl'
        self.fail_path = self.local/f'{name}.failed.jsonl'
        self._restore_from_mirror()
        self.done, self.failed = self._load()

    # ---- mirror handling -------------------------------------------------
    def _restore_from_mirror(self):
        """If local disk was wiped (new runtime) but Drive has state, pull it back."""
        if not self.mirror: return
        for p in (self.data_path, self.fail_path):
            m = self.mirror/p.name
            if m.exists() and (not p.exists() or m.stat().st_size > p.stat().st_size):
                shutil.copy2(m, p)

    def _push_mirror(self):
        if not self.mirror: return
        try:
            for p in (self.data_path, self.fail_path):
                if p.exists(): shutil.copy2(p, self.mirror/p.name)
        except Exception as e:
            print(f'  [mirror warning: {e}]')   # never fatal

    # ---- state -----------------------------------------------------------
    def _load(self):
        done, failed = {}, {}
        if self.data_path.exists():
            with open(self.data_path) as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        done[r['_key']] = r
                    except Exception:
                        continue          # truncated final line after a crash
        if self.fail_path.exists():
            with open(self.fail_path) as f:
                for line in f:
                    try:
                        r = json.loads(line); failed[r['_key']] = r.get('n', 1)
                    except Exception:
                        continue
        return done, failed

    def pending(self, keys):
        """O(n) resume: skip completed and permanently-failed keys."""
        d, fl, m = self.done, self.failed, self.max_attempts
        return [k for k in keys if k not in d and fl.get(k, 0) < m]

    # ---- the run loop ----------------------------------------------------
    def run(self, keys, fn, progress=True):
        """Workers write their OWN results the moment they complete.

        The earlier version wrote from the consumer side of ThreadPoolExecutor.map().
        That is wrong: map() submits everything eagerly, so workers can finish
        thousands of items while the consumer lags behind, and every one of those
        is lost on a hard kill. Writing inside the worker, under a lock, means a
        completed item is durable the moment it exists.
        """
        import threading
        todo = self.pending(keys)
        print(f'[{self.name}] total={len(keys):,}  done={len(self.done):,}  '
              f'failed={len(self.failed):,}  todo={len(todo):,}')
        if not todo:
            print(f'[{self.name}] nothing to do — already complete.')
            return self.frame()

        lock = threading.Lock()
        fd = open(self.data_path, 'a'); ff = open(self.fail_path, 'a')
        counters = {'ok': 0, 'bad': 0, 'since_flush': 0, 'since_mirror': 0}
        t0 = time.time()

        def worker(key):
            try:
                rec = fn(key)
            except Exception:
                rec = None
            with lock:
                if rec is None:
                    counters['bad'] += 1
                    n = self.failed.get(key, 0) + 1
                    ff.write(json.dumps({'_key': key, 'n': n}) + '\n')
                    self.failed[key] = n
                else:
                    counters['ok'] += 1
                    r = dict(rec); r['_key'] = key
                    fd.write(json.dumps(r, default=str) + '\n')
                    self.done[key] = r
                counters['since_flush'] += 1
                counters['since_mirror'] += 1
                if counters['since_flush'] >= self.flush_every:
                    fd.flush(); os.fsync(fd.fileno())
                    ff.flush(); os.fsync(ff.fileno())
                    counters['since_flush'] = 0
                due = (counters['since_mirror'] >= self.mirror_every or
                       time.time() - self._last_mirror >= self.mirror_seconds)
                if due:
                    fd.flush(); ff.flush(); self._push_mirror()
                    counters['since_mirror'] = 0; self._last_mirror = time.time()
            return key

        try:
            from tqdm.auto import tqdm
            wrap = (lambda it: tqdm(it, total=len(todo))) if progress else (lambda it: it)
        except Exception:
            wrap = lambda it: it

        try:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                for _ in wrap(ex.map(worker, todo)):
                    pass
        except KeyboardInterrupt:
            print(f'\n[{self.name}] INTERRUPTED — progress is safe. Re-run to resume.')
        finally:
            try:
                fd.flush(); os.fsync(fd.fileno()); fd.close()
                ff.flush(); os.fsync(ff.fileno()); ff.close()
            except Exception: pass
            self._push_mirror()

        print(f'[{self.name}] +{counters["ok"]:,} ok, +{counters["bad"]:,} failed '
              f'in {time.time()-t0:.0f}s -> {len(self.done):,} total')
        return self.frame()

    def frame(self):
        import pandas as pd
        if not self.done: return pd.DataFrame()
        df = pd.DataFrame(list(self.done.values()))
        return df.rename(columns={'_key': 'project'})


class CellState:
    """Records which cells completed, so a fresh runtime tells you where you were."""
    def __init__(self, path):
        self.path = Path(path); self.state = {}
        if self.path.exists():
            try: self.state = json.loads(self.path.read_text())
            except Exception: self.state = {}

    def mark(self, cell):
        self.state[str(cell)] = time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        atomic_write_bytes(self.path, json.dumps(self.state, indent=2).encode())

    def report(self):
        if not self.state:
            print('No previous run recorded — start at cell 1.'); return
        print('Previously completed cells:')
        for k in sorted(self.state, key=lambda x: int(x)):
            print(f'   cell {k}: {self.state[k]}')
        nxt = max(int(k) for k in self.state) + 1
        print(f'-> After a disconnect, re-run cells 1..{nxt-1} (they are cached '
              f'and fast), then continue at cell {nxt}.')
