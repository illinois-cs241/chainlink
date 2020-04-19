import asyncio
import concurrent
import concurrent.futures
import logging
import os
import tempfile

import docker
import docker.errors

# set up module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Chainlink:
    """
    A utility for running docker containers sequentially
    """

    def __init__(self, stages, workdir="/tmp", max_workers=4):
        self.client = docker.from_env()
        self.stages = stages
        self.workdir = workdir
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers)

    def run(self, *args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(
            self.run_async(*args, **kwargs)
        )

    async def run_async(self, environ={}):
        results = []

        await self._pull_images()

        with tempfile.TemporaryDirectory(dir=self.workdir) as mount:
            logger.info("using {} for temporary job directory".format(mount))
            os.chmod(mount, 0o777)

            for (idx, stage) in enumerate(self.stages):
                logger.info("running stage {}".format(idx + 1))
                results.append(await self._run_stage(stage, mount, environ))
                if not results[-1]["success"]:
                    logger.error("stage {} was unsuccessful".format(idx + 1))
                    break
                else:
                    logger.info("stage {} was successful".format(idx + 1))

        return results

    async def _pull_images(self):
        images = set([stage["image"] for stage in self.stages])
        tasks = []

        for image in images:
            logger.debug("pulling image '{}'".format(image))

            tasks.append(self._pull_image(image))

        try:
            await asyncio.gather(*tasks)
        except docker.errors.ImageNotFound:
            logger.error("image '{}' not found remotely or locally".format(image))
        except docker.errors.APIError as err:
            logger.error("Docker API Error: {}".format(err))

    async def _pull_image(self, image):
        def wait():
            try:
                return self.client.images.pull(image)
            except docker.errors.NotFound:
                # if not found on docker hub, try locally
                logger.info(
                    "image '{}' not found on Docker Hub, fetching locally".format(image)
                )
                return self.client.images.get(image)

        return await asyncio.get_event_loop().run_in_executor(self._executor, wait)

    async def _run_stage(self, stage, mount, environ):
        environ = {**environ, **stage.get("env", {})}
        volumes = {mount: {"bind": "/job", "mode": "rw"}}

        # TODO find a way to set disk limit?
        options = {
            "cpu_period": 100000,  # microseconds
            "detach": True,
            "entrypoint": stage.get("entrypoint", None),
            "environment": environ,
            "hostname": stage.get("hostname", "container"),
            "ipc_mode": "private",
            "mem_limit": stage.get("memory", "2g"),
            "memswap_limit": stage.get("memory", "2g"),  # same as memory, so no swap
            "network_disabled": not stage.get("networking", True),
            "privileged": stage.get("privileged", False),
            "volumes": volumes,
            "tty": True,
        }

        container, killed = await self._wait_for_stage(stage, options)
        result = {
            "data": self.client.api.inspect_container(container.id)["State"],
            "killed": killed,
            "logs": {"stdout": None, "stderr": None},
        }
        if stage.get("logs", True):
            result["logs"]["stdout"] = container.logs(stderr=False, timestamps=True)
            result["logs"]["stderr"] = container.logs(stdout=False, timestamps=True)

        result["success"] = (not killed) and (result["data"]["ExitCode"] == 0)
        container.remove()

        return result

    async def _wait_for_stage(self, stage, options):
        timeout = stage.get("timeout", 30)
        container = self.client.containers.run(stage["image"], **options)
        event_loop = asyncio.get_event_loop()

        # execute and wait
        try:
            await asyncio.wait_for(
                event_loop.run_in_executor(self._executor, container.wait),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error("killing container after {} seconds".format(timeout))
            container.kill()
            return container, True

        return container, False

    def __del__(self):
        self.client.close()
