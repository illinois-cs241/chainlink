import docker
import json
import logging
import os.path as path
import queue
import stopit
import tempfile
import threading
import time

# set up module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# turn off stopit's verbose logger
stopit_logger = logging.getLogger('stopit')
stopit_logger.setLevel(logging.ERROR)

class Chainlink:
  """
  A utility for running docker containers sequentially
  """

  def __init__(self, stages, workdir="/tmp"):
    self.client = docker.from_env()
    self.stages = stages
    self.workdir = workdir
    self._pull_images()

  def run(self, environ):
    results = []
    with tempfile.TemporaryDirectory(dir=self.workdir) as mount:
      logger.info("using {} for temporary job directory".format(mount))
      
      for (idx, stage) in enumerate(self.stages):
        logger.info("running stage {}".format(idx + 1))
        results.append(self._run_stage(stage, mount, environ))
        if not results[-1]["success"]:
          logger.error("stage {} was unsuccessful".format(idx + 1))
          break
        else:
          logger.info("stage {} was successful".format(idx + 1))

    return results

  def _pull_images(self):
    images = set([stage["image"] for stage in self.stages])
    threads = []

    for image in images:
      logger.debug("pulling image '{}'".format(image))
      t = threading.Thread(target=self.client.images.pull, args=(image,))
      t.start()
      threads.append(t)
    for t in threads:
      t.join()

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
      "cap_add": stage.get("capabilities", []),
      "volumes": volumes,
      "tty": True
    }

    container, killed = self._wait_for_stage(stage, options)
    result = {
      "data": self.client.api.inspect_container(container.id)["State"],
      "killed": killed,
      "logs": container.logs(timestamps=True),
    }
    result["success"] = (not killed) and (result["data"]["ExitCode"] == 0)
    container.remove()

    return result

  def _wait_for_stage(self, stage, options):
    timeout = stage.get("timeout", 30)
    container = self.client.containers.run(stage["image"], **options)
    killed = True

    with stopit.ThreadingTimeout(timeout) as timeout_ctx:
      assert timeout_ctx.state == timeout_ctx.EXECUTING 
      container.wait()

    if timeout_ctx.state == timeout_ctx.EXECUTED:
      killed = False
    elif timeout_ctx.state == timeout_ctx.TIMED_OUT:
      logger.error("killed stage after {} seconds".format(timeout))
      container.kill()
    else:
      logger.error("unexpected timeout context state '{}'".format(timeout_ctx.state))

    return container, killed

  def __del__(self):
    self.client.close()
