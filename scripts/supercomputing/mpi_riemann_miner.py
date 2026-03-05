"""
MPI Multi-Node Dispatch for Riemann-Zero Mining.

Replaces `ProcessPoolExecutor` with `mpi4py` to allow zeta zero mining
to scale across an arbitrary number of PHYSICAL nodes in a Supercomputing cluster.

Usage:
    mpirun -np 128 python scripts/supercomputing/mpi_riemann_miner.py --t_start 10000 --t_end 20000
"""
import sys
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

try:
    from mpi4py import MPI
except ImportError:
    print("FATAL: mpi4py is required. Install with: pip install mpi4py")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock import for Riemann mining logic (replace with actual function from engine)
# from src.zeta_miner import find_zeros_in_range

def mock_find_zeros_in_range(t_start, t_end, resolution):
    """Placeholder for the actual zeta function evaluator."""
    # Simulates finding zeros
    return [{"t": t_start + 0.5, "imaginary": True}]

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    ap = argparse.ArgumentParser()
    ap.add_argument("--t_start", type=float, required=True, help="Start of imaginary t range")
    ap.add_argument("--t_end", type=float, required=True, help="End of imaginary t range")
    ap.add_argument("--resolution", type=float, default=0.1, help="Step size for root finding")
    args = ap.parse_args()

    # -----------------------------------------------------------------------
    # NODE 0: Partition the t-space
    # -----------------------------------------------------------------------
    if rank == 0:
        print("=" * 70)
        print(f" RIEMANN-ZERO MPI SUPERCOMPUTING DISPATCH")
        print(f" Range: [{args.t_start}, {args.t_end}] | Cluster Workers: {size}")
        print("=" * 70)

        total_range = args.t_end - args.t_start
        chunk_size = total_range / size
        
        chunks = []
        for i in range(size):
            chunks.append((args.t_start + (i * chunk_size), args.t_start + ((i + 1) * chunk_size)))
        start_time = time.time()
    else:
        chunks = None

    # SCATTER
    my_chunk = comm.scatter(chunks, root=0)

    # PROCESS
    my_t_start, my_t_end = my_chunk
    # local_zeros = find_zeros_in_range(my_t_start, my_t_end, args.resolution)
    local_zeros = mock_find_zeros_in_range(my_t_start, my_t_end, args.resolution)

    # GATHER
    all_zeros_lists = comm.gather(local_zeros, root=0)

    # NODE 0: Aggregation
    if rank == 0:
        elapsed = time.time() - start_time
        all_zeros = [item for sublist in all_zeros_lists for item in sublist]
        n_zeros = len(all_zeros)

        out_dir = Path("evidence/supercomputing")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "cluster_size": size,
            "t_range": [args.t_start, args.t_end],
            "n_zeros_found": n_zeros,
            "wall_time_s": round(elapsed, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        mf_path = out_dir / f"mpi_manifest_riemann_{int(args.t_start)}.json"
        mf_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        print(f"\n{'=' * 70}")
        print(f" MPI RUN COMPLETE | Zeros found: {n_zeros}")
        print(f" Total Time: {elapsed:.1f}s")
        print(f" Evidence saved to: {out_dir}")
        print(f" {'=' * 70}")

if __name__ == "__main__":
    main()
