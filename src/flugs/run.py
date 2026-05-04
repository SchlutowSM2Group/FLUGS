"""FLUGS inversion runner — invoked by ``python -m flugs -c <config>``."""

import logging
from datetime import datetime

from .config import OUTPUT_DIR
from .footprint_interface import get_footprints
from .inversion import (
    compute_weight_matrix,
    generate_kernel_matrix,
    run_optimizer_eig,
)
from .prepare import get_data
from .utils import array_utils as au
from .utils.io import create_run_dir, save_data, save_metadata
from .utils.logging import setup_logging


def main():
    """Run the full inversion pipeline for one YAML configuration.

    Reads ``-c <config>`` (and optionally ``-r <run_name>``) from ``sys.argv``,
    computes BLDFM footprints, builds the weight and kernel matrices, solves
    the regularised inversion via the Visick (2000) eigendecomposition of the
    weighted kernel, and writes the per-land-cover-group scaling factors plus
    run metadata to a timestamped directory under ``OUTPUT_DIR``.
    """
    start_time = datetime.now()

    run_config, sim_data = get_data()

    run_dir = create_run_dir(OUTPUT_DIR, run_config.run_name)
    setup_logging(
        namespace="flugs",
        level=logging.DEBUG,
        log_file="run.log",
        log_dir=run_dir,
        auto_file=False,
    )

    logging.info(f"Run directory: {run_dir}")

    footprints, fp_success = get_footprints(run_config, sim_data)

    n_failed = int((~fp_success).sum())
    if n_failed > 0:
        logging.info(
            f"Excluding {n_failed} timestep(s) with failed footprint computation."
        )
        footprints = footprints[fp_success]
        sim_data.measurement_data = sim_data.measurement_data[fp_success].reset_index(
            drop=True
        )
        sim_data.N = int(fp_success.sum())

    weight_matrix = compute_weight_matrix(footprints, run_config, sim_data)
    kernel_matrix = generate_kernel_matrix(run_config, sim_data)

    scaling_factors, statistics = run_optimizer_eig(
        kernel_matrix, weight_matrix, run_config, sim_data
    )
    cost_func = None

    for key, value in statistics.items():
        logging.info(f"{key} = {value}")

    out_arr, col_names = au.prepare_output(scaling_factors, run_config, sim_data)
    save_data(f"{run_dir}/{run_config.run_name}_flugs.csv", out_arr, col_names)

    end_time = datetime.now()
    save_metadata(
        run_dir, run_config, sim_data, statistics, cost_func, start_time, end_time
    )
    logging.info(f"Metadata saved to {run_dir}/metadata.json")


if __name__ == "__main__":
    main()
