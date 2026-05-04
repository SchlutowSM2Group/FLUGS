"""Inversion core: weight matrix, kernel matrix, and Visick eigendecomposition solver."""

import numpy as np

from .utils.data_classes import SimData, RunConfig
from .utils.array_utils import get_df_col
from .utils.diagnostics import get_statistics
from .footprint_interface import point_measurement


def compute_weight_matrix(
    footprints: np.ndarray, run_config: RunConfig, sim_data: SimData
) -> np.ndarray:
    """Convolve each footprint with each land-cover-group mask.

    Parameters
    ----------
    footprints : ndarray, shape (N, ny, nx)
        Per-timestep footprint sensitivity fields from BLDFM.
    run_config : RunConfig
    sim_data : SimData

    Returns
    -------
    ndarray, shape (N, I_gtyp)
        Weight matrix ``W[n, g] = ∫ mask_g(x) · footprint_n(x) dx``.
    """
    N = sim_data.N
    weight_matrix_group = np.zeros(N)
    weight_matrix = np.zeros((N, run_config.landcover.I_gtyp))

    for g_idx in range(run_config.landcover.I_gtyp):
        srf_flx = sim_data.land_cover_by_group[g_idx, ...].copy()
        srf_flx[~np.isnan(srf_flx)] = 1.0
        srf_flx = np.nan_to_num(srf_flx, nan=0.0)

        for n in range(N):
            weight_matrix_group[n] = point_measurement(srf_flx, footprints[n, ...])

        weight_matrix[:, g_idx] = weight_matrix_group

    return weight_matrix


def _build_kernel_matrix(run_config: RunConfig, sim_data: SimData) -> np.ndarray:
    """Build the (N x N) kernel matrix from normalised driver variables."""
    from sklearn.metrics.pairwise import polynomial_kernel, rbf_kernel

    N = sim_data.N
    D = run_config.dataset.D
    measurement_data = sim_data.measurement_data

    kernel = run_config.inversion.kernel_type
    gamma = run_config.inversion.gamma

    X = np.zeros((D, N))
    for d, driver_var_name in enumerate(run_config.dataset.driver_variables):
        driver = get_df_col(measurement_data, driver_var_name)
        driver_min = np.min(driver)
        driver_max = np.max(driver)
        X[d, :] = (driver - driver_min) / (driver_max - driver_min)

    if kernel == "linear":
        K = polynomial_kernel(X.T, degree=1, gamma=None, coef0=1)
    if kernel == "polynomial":
        K = polynomial_kernel(X.T, degree=2, gamma=None, coef0=1)
    if kernel == "rbf":
        K = rbf_kernel(X.T, gamma=gamma)

    return K


def generate_kernel_matrix(run_config: RunConfig, sim_data: SimData) -> np.ndarray:
    """Return the (N x N) kernel matrix K."""
    return _build_kernel_matrix(run_config, sim_data)


def run_optimizer_eig(
    kernel_mat: np.ndarray,
    weight_mat: np.ndarray,
    run_data: RunConfig,
    sim_data: SimData,
) -> tuple[np.ndarray, dict]:
    """Eigendecomposition-based KRR solver (Visick 2000).

    Solves the weighted-kernel ridge regression problem
    ``[K ⊙ (W W^T) + λI] α = y`` via the symmetric eigendecomposition
    ``K_w = V Λ V^T``, giving ``α = V (Λ + λI)^{-1} V^T y``.

    Parameters
    ----------
    kernel_mat : ndarray, shape (N, N)
        Driver-variable kernel matrix ``K`` from :func:`generate_kernel_matrix`.
    weight_mat : ndarray, shape (N, I_gtyp)
        Footprint × land-cover weight matrix from :func:`compute_weight_matrix`.
    run_data : RunConfig
    sim_data : SimData

    Returns
    -------
    scaling_factors : ndarray, shape (N, I_gtyp)
        Per-LCC ERF weights ``S = (W^T diag(α) K)^T``.
    statistics : dict
        Output of :func:`flugs.utils.diagnostics.get_statistics`.
    """
    from scipy.linalg import eigh

    reg = run_data.inversion.regularization_parameter

    target = get_df_col(sim_data.measurement_data, run_data.observation_variable)

    weighted_ker_mat = kernel_mat * (weight_mat @ weight_mat.T)

    eigvals, eigvecs = eigh(weighted_ker_mat)

    dual_coeffs = eigvecs @ ((1.0 / (eigvals + reg)) * (eigvecs.T @ target))

    scaling_factors = (weight_mat.T @ (dual_coeffs[:, None] * kernel_mat)).T

    model = weighted_ker_mat @ dual_coeffs
    statistics = get_statistics(model, target)

    return scaling_factors, statistics
