"""
Priority Queue — Separates critical data from routine data for transmission.

Critical data (anomalies, resource alerts) gets immediate transmission priority.
Routine data is batched for later transmission.
"""

from collections import deque


class PriorityDataQueue:
    """Priority queue that separates critical and routine data for transmission."""

    def __init__(self):
        self.critical_queue = deque()
        self.normal_queue = deque()
        self.total_critical = 0
        self.total_normal = 0

    def enqueue(self, data: dict, priority: str = "normal"):
        """
        Add data to the appropriate queue.
        
        Args:
            data: Data payload
            priority: 'critical' or 'normal'
        """
        if priority == "critical":
            self.critical_queue.append(data)
            self.total_critical += 1
        else:
            self.normal_queue.append(data)
            self.total_normal += 1

    def dequeue_critical(self) -> list:
        """Get all critical data items (returns and clears critical queue)."""
        items = list(self.critical_queue)
        self.critical_queue.clear()
        return items

    def dequeue_normal(self, batch_size: int = 10) -> list:
        """Get a batch of normal data items."""
        items = []
        for _ in range(min(batch_size, len(self.normal_queue))):
            items.append(self.normal_queue.popleft())
        return items

    def has_critical(self) -> bool:
        """Check if there's critical data waiting."""
        return len(self.critical_queue) > 0

    def get_stats(self) -> dict:
        return {
            "critical_pending": len(self.critical_queue),
            "normal_pending": len(self.normal_queue),
            "total_critical_processed": self.total_critical,
            "total_normal_processed": self.total_normal,
        }
