#!/bin/bash
#SBATCH --job-name="dataEncoder"
#SBATCH --partition production
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mem=64GB


# change to the working directory
cd $SLURM_WORKDIR

echo ">>>> Begin dataEncoder"

python $(pwd)/cp_learning/ae_processor.py  --encode --filtered --data_dir $(pwd)/pickled --storage_path $(pwd)/encoded --batch_size 6 --num_workers 15 --embed_size 96 --hidden_size 256 --checkpoint_path /global/u/shawn_bc_10/checkpoints/epoch-40-step-178853.ckpt
