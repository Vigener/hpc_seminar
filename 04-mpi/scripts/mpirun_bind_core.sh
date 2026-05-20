#!/usr/bin/env bash
# Wrapper to force mpirun to bind ranks to cores
# Adjust underlying mpirun path if needed
exec mpirun --bind-to core --map-by core "$@"
