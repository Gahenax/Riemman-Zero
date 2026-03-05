#!/bin/bash
#PBS -N Gahenax_Riemann
#PBS -o logs/riemann_mpi.out
#PBS -e logs/riemann_mpi.err
#PBS -l nodes=4:ppn=32
#PBS -l walltime=48:00:00
#PBS -q batch
#PBS -l pmem=2gb

cd $PBS_O_WORKDIR
module purge
module load python/3.10 openmpi/4.1.4
source venv/bin/activate
export PYTHONPATH=$(pwd)

echo "Starting Riemann-Zero on PBS Cluster."
mpiexec python scripts/supercomputing/mpi_riemann_miner.py --t_start 100000 --t_end 200000
