"""
Auris Pipeline - Engine
Chains processors together and runs them concurrently.
Written from scratch.
"""
import asyncio
from loguru import logger

from app.services.pipeline.base_processor import BaseProcessor
from app.services.pipeline.frame import Frame


class PipelineEngine:
    """
    Connects a list of processors in order:
      processors[0] → processors[1] → ... → processors[N]

    Output queue of processor[i] is wired to input queue of processor[i+1]
    via a forwarding task.
    """

    def __init__(self, processors: list[BaseProcessor]):
        if not processors:
            raise ValueError("Pipeline must have at least one processor")
        self.processors = processors
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def _wire(self) -> None:
        """Wire output of processor[i] → input of processor[i+1]."""
        for i in range(len(self.processors) - 1):
            src = self.processors[i]
            dst = self.processors[i + 1]

            async def forward(s=src, d=dst):
                while True:
                    frame = await s.output.get()
                    await d.input.put(frame)
                    if frame is None:
                        break

            self._tasks.append(asyncio.create_task(forward(), name=f"wire-{src.name}->{dst.name}"))

    async def start(self) -> None:
        """Start all processors and wire them together."""
        self._running = True
        self._wire()
        for p in self.processors:
            self._tasks.append(asyncio.create_task(p.run(), name=f"proc-{p.name}"))
        logger.info(f"Pipeline started with {len(self.processors)} processors: "
                    f"{[p.name for p in self.processors]}")

    async def push(self, frame: Frame) -> None:
        """Push a frame into the first processor."""
        await self.processors[0].push(frame)

    async def collect(self) -> Frame | None:
        """Read one frame from the last processor's output."""
        return await self.processors[-1].output.get()

    async def stop(self) -> None:
        """Gracefully stop the pipeline."""
        self._running = False
        await self.processors[0].stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Pipeline stopped")

    async def run_until_done(self) -> None:
        """Run until the last processor emits None (call ended)."""
        await self.start()
        while True:
            frame = await self.collect()
            if frame is None:
                break
        await self.stop()
