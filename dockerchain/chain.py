import docker
import json
import os.path as path
import stopit
import tempfile
import time

class DockerChain:
  def __init__(self, stages, workdir="/tmp"):
    self.client = docker.from_env()
    self.stages = stages
    self.workdir = workdir
    self._pull_images()

  def run(self, environ, roster=None):
    results = []
    with tempfile.TemporaryDirectory(dir=self.workdir) as mount:
      if roster:
        self._install_roster(mount, roster)
      
      for (idx, stage) in enumerate(self.stages):
        results.append(self._run_stage(stage, mount, environ))
        if not results[-1]["success"]:
          # TODO log failure
          break

    # TODO provide some overall indication of success?
    return results

  def _pull_images(self):
    images = [stage["image"] for stage in self.stages]
    for image in set(images):
      self.client.pull(image)

  def _install_roster(self, mount, roster):
    with open(path.join(mount, "roster.json")) as roster_file:
      json.dump(roster, roster_file)

  def _run_stage(self, stage, mount, environ):
    environ = { **environ, **stage.get("env", {}) }
    volumes = {}
    volumes[mount] = { "bind": "/job", "mode": "rw" }

    # TODO find a way to set disk limit?
    options = {
      "cpu_period": 100000, # microseconds
      "cpu_quota": 90000, # container consumes up to 90% CPU
      "detach": True,
      "entrypoint": stage.get("entrypoint", None),
      "environment": environ,
      "hostname": stage.get("hostname", "container"),
      "ipc_mode": "private",
      "mem_limit": stage.get("memory", "2g"),
      "memswap_limit": stage.get("memory", "2g"), # same as memory, so no swap
      "network_disabled": not stage.get("networking", True),
      "volumes": volumes,
      "tty": True
    }

    container, killed = self._wait_for_stage(stage, options)
    result = {
      "data": self.client.api.inspect_container(container.id),
      "killed": killed,
      "logs": container.logs(timestamps=True),
    }
    result["success"] = (not killed) and (result["data"]["State"]["ExitCode"] == 0)
    container.remove()

    return result

  def _wait_for_stage(self, stage, options):
    timeout = stage.get("timeout", 30)
    container = self.containers.run(stage["image"], **options)
    killed = True

    with stopit.ThreadingTimeout(timeout) as timeout_ctx:
      assert timeout_ctx.state == timeout_ctx.EXECUTING 
      container.wait()

    if to_ctx_mgr.state == to_ctx_mgr.EXECUTED:
      killed = False
    elif to_ctx_mgr.state == to_ctx_mgr.TIMED_OUT:
      container.kill()
    else:
      # TODO there's an unexpected error, log about it

    return container, killed
