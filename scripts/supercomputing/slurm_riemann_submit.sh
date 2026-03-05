#!/bin/bash
#SBATCH --job-name=Gahenax_Riemann
#SBATCH --output=logs/riemann_mpi_%j.out
#SBATCH --nodes=4                   
#SBATCH --ntasks-per-node=32        
#SBATCH --time=48:00:00             
#SBATCH --partition=compute         

module purge
module load python/3.10 openmpi/4.1.4
source venv/bin/activate
export PYTHONPATH=$(pwd)

echo "Starting Riemann-Zero on $SLURM_JOB_NUM_NODES nodes."
mpirun python scripts/supercomputing/mpi_riemann_miner.py --t_start 100000 --t_end 200000
