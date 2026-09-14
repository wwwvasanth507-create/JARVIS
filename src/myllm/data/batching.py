"""
CPU Batch Generator for MyLLM.

Constructs training batches of PyTorch CPU tensors (input_ids [B, T] and labels [B, T])
from memory-mapped TokenDataset instances.
"""

from __future__ import annotations

import random
from typing import Generator, Iterator, Optional, Tuple
import numpy as np
import torch
from myllm.data.dataset import TokenDataset


class BatchGenerator:
    """
    CPU Batch Generator for training GPTModel.

    Produces batches of PyTorch CPU tensors with integer dtype torch.long:
        input_ids: [B, T]
        labels:    [B, T] (shifted by 1 token)
    """

    def __init__(
        self,
        dataset: TokenDataset,
        batch_size: int = 8,
        shuffle: bool = True,
        seed: Optional[int] = None,
        drop_last: bool = False,
    ) -> None:
        if len(dataset) == 0:
            raise ValueError("Cannot create BatchGenerator for empty dataset.")
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.drop_last = drop_last

        self._rng = random.Random(seed) if seed is not None else random.Random()

    def __len__(self) -> int:
        if self.drop_last:
            return len(self.dataset) // self.batch_size
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size

    def get_random_batch(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Sample a single random batch of size [B, T] on CPU.

        Returns:
            Tuple of (input_ids, labels) CPU tensors.
        """
        indices = [self._rng.randint(0, len(self.dataset) - 1) for _ in range(self.batch_size)]
        xs = []
        ys = []
        for idx in indices:
            x, y = self.dataset[idx]
            xs.append(x)
            ys.append(y)

        input_ids = torch.from_numpy(np.stack(xs)).long().to("cpu")
        labels = torch.from_numpy(np.stack(ys)).long().to("cpu")
        return input_ids, labels

    def __iter__(self) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
        indices = list(range(len(self.dataset)))
        if self.shuffle:
            self._rng.shuffle(indices)

        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i : i + self.batch_size]
            if self.drop_last and len(batch_indices) < self.batch_size:
                break

            xs = []
            ys = []
            for idx in batch_indices:
                x, y = self.dataset[idx]
                xs.append(x)
                ys.append(y)

            input_ids = torch.from_numpy(np.stack(xs)).long().to("cpu")
            labels = torch.from_numpy(np.stack(ys)).long().to("cpu")
            yield input_ids, labels
