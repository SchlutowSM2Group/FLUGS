"""Inversion core: weight matrix, kernel/design matrix, and CG solver."""

import logging

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


def generate_design_matrix(run_config: RunConfig, sim_data: SimData) -> np.ndarray:
    """Return ``K^{1/2}`` (principal square root) as the design matrix."""
    from scipy.linalg import sqrtm

    K = _build_kernel_matrix(run_config, sim_data)
    return sqrtm(K).real.T


def flugs_quattro_matvec(x, L, W, U, V):
    """Compute ``[(L^T ⊗ W)^T S (U^T ⊗ V)] @ x`` without forming the full matrix.

    Identity exploited::

        [(L^T ⊗ W)^T S (U^T ⊗ V)]_{pi, qj} = Σ_n L_{pn} U_{qn} W_{ni} V_{nj}

    Parameters
    ----------
    x : ndarray, shape (Q*J,)
    L : ndarray, shape (P, N)
    W : ndarray, shape (N, I)
    U : ndarray, shape (Q, N)
    V : ndarray, shape (N, J)

    Returns
    -------
    ndarray, shape (P*I,)
    """
    Q, J = U.shape[0], V.shape[1]
    X = x.reshape(Q, J)
    Z = np.sum(U * (X @ V.T), axis=0)
    return ((L * Z) @ W).flatten()


def _solve_inversion(design_matrix, weight_matrix, target, reg, N, I, P):
    """Conjugate-gradient solve of the regularized normal equations.

    Solves::

        [(L^T ⊗ W)^T (L^T ⊗ W) + λI] bvec = (L ⊗ W)^T target

    Returns ``(bvec, info)`` where *info* is the scipy CG convergence flag.
    """
    from scipy.sparse.linalg import cg, LinearOperator

    L = design_matrix
    W = weight_matrix

    def cmat_matvec(x):
        return flugs_quattro_matvec(x, L.T, W, L.T, W) + reg * x

    cmat = LinearOperator(shape=(I * P, I * P), matvec=cmat_matvec, dtype=np.float64)

    ovec = np.ones((1, N))
    idN = np.eye(N)
    rhs = flugs_quattro_matvec(target, L, W, ovec, idN)

    bvec, info = cg(cmat, rhs, atol=1e-10)
    if info != 0:
        logging.warning(f"Conjugate gradient did not converge, info={info}")

    return bvec, info


def run_optimizer(
    design_matrix: np.ndarray,
    weight_matrix: np.ndarray,
    run_data: RunConfig,
    sim_data: SimData,
) -> tuple[np.ndarray, dict, float]:
    """CG-based KRR solver.

    Parameters
    ----------
    design_matrix : ndarray, shape (N, P)
        Temporal design matrix ``L = K^{1/2}``.
    weight_matrix : ndarray, shape (N, I_gtyp)
        Footprint × land-cover weight matrix from :func:`compute_weight_matrix`.
    run_data : RunConfig
    sim_data : SimData

    Returns
    -------
    scaling_factors : ndarray, shape (N, I_gtyp)
    statistics : dict
        Output of :func:`flugs.utils.diagnostics.get_statistics`.
    cost_function : float
        ``||W S^T - y||² + λ ||bvec||²``.
    """
    N = sim_data.N
    I = run_data.landcover.I_gtyp
    P = design_matrix.shape[1]

    reg = run_data.inversion.regularization_parameter

    logging.info(f"N = {N}, I = {I}, P = {P}")

    target = get_df_col(sim_data.measurement_data, run_data.observation_variable)

    bvec, info = _solve_inversion(design_matrix, weight_matrix, target, reg, N, I, P)

    B = bvec.reshape(P, I)
    avec = (design_matrix @ B).flatten()
    scaling_factors = avec.reshape((N, I))

    model = np.diagonal(weight_matrix @ scaling_factors.T)
    statistics = get_statistics(model, target)
    cost_function = np.sum((model - target) ** 2) + reg * np.sum(bvec**2)

    return scaling_factors, statistics, cost_function
