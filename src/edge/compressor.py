"""
Data Compressor — Estimates payload compression for bandwidth reduction.

Simulates compression of data payloads to reduce network transmission costs.
"""


class DataCompressor:
    """Simulates data compression for edge processing."""

    def __init__(self, compression_ratio: float = 0.6):
        """
        Args:
            compression_ratio: Ratio of compressed size to original size.
                              0.6 means compressed data is 60% of original.
        """
        self.compression_ratio = compression_ratio
        self.total_original_bytes = 0
        self.total_compressed_bytes = 0

    def estimate_compressed_size(self, original_bytes: int) -> int:
        """
        Estimate compressed payload size.
        
        Args:
            original_bytes: Original payload size in bytes
            
        Returns:
            Estimated compressed size in bytes
        """
        compressed = int(original_bytes * self.compression_ratio)
        self.total_original_bytes += original_bytes
        self.total_compressed_bytes += compressed
        return compressed

    def get_savings_pct(self) -> float:
        """Return percentage of bytes saved by compression."""
        if self.total_original_bytes == 0:
            return 0.0
        saved = self.total_original_bytes - self.total_compressed_bytes
        return (saved / self.total_original_bytes) * 100.0

    def get_stats(self) -> dict:
        return {
            "compression_ratio": self.compression_ratio,
            "total_original_bytes": self.total_original_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "savings_pct": round(self.get_savings_pct(), 1),
        }
