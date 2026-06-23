"""
Auris Pipeline - Base Processor.
Every stage in the pipeline inherits from this.
Written from scratch.
"""
import asyncio
from abc import ABC, abstractmethod

from app.services.pipeline.frame import Frame


class BaseProcessor(ABC):
    """
    A processor receives frames from an input queue,
    processes them, and pushes results to an output queue.

    Subclass and implement `process_frame(frame)`.
    """

    def __init__(self, name: str):
        self.name = name
        self._input: asyncio.Queue[Frame | None] = asyncio.Queue()
        self._output: asyncio.Queue[Frame | None] = asyncio.Queue()
        self._running = False

    @property
    def input(self) -> asyncio.Queue:
        return self._input

    @property
    def output(self) -> asyncio.Queue:
        return self._output

    async def push(self, frame: Frame) -> None:
        """Push a frame into this processor's input queue."""
        await self._input.put(frame)

    async def emit(self, frame: Frame) -> None:
        """Emit a frame to the output queue (called from subclasses)."""
        await self._output.put(frame)

    @abstractmethod
    async def process_frame(self, frame: Frame) -> None:
        """
        Handle one frame. Call self.emit(frame) to pass frames downstream.
        Can emit zero, one, or multiple frames per input frame.
        """

    async def run(self) -> None:
        """Drain the input queue until None sentinel is received."""
        self._running = True
        while self._running:
            frame = await self._input.get()
            if frame is None:
                # Propagate shutdown sentinel downstream
                await self._output.put(None)
                break
            try:
                await self.process_frame(frame)
            except Exception as e:
                from app.services.pipeline.frame import FrameType, error_frame
                await self.emit(error_frame(f"{self.name}: {e}"))

    async def stop(self) -> None:
        self._running = False
        await self._input.put(None)  # unblock run()

    def __repr__(self) -> str:
        return f"<Processor:{self.name}>"
