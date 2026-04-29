from pathlib import Path

import pandas as pd
from numpy.typing import NDArray

from dataclasses import dataclass, field
from typing import List
from ..config import CONFIG_DIR, DATA_DIR


@dataclass
class ProjectConfig:
    data_dir: Path = field(default_factory=lambda: Path(DATA_DIR))
    config_dir: Path = field(default_factory=lambda: Path(CONFIG_DIR))


@dataclass
class DatasetParams:
    _project_config: ProjectConfig

    csv_filename: str
    biomet_filename: str

    driver_variables: List[str]

    source_row: int
    source_col: int
    measurement_height: float

    latitude_extent: list
    longitude_extent: list

    start_date: str
    end_date: str

    # measurements to keep
    measurements_to_keep = [
        "date",
        "time",
        "H",
        "qc_H",
        "LE",
        "qc_LE",
        "air_temperature",
        "air_density",
        "air_heat_capacity",
        "u_rot",
        "wind_dir",
        "u*",
        "(z-d)/L",
        "L",
        "RH",
    ]

    # quality level of dataset to filter
    quality_level_to_keep: int = 2

    @property
    def csv_path(self):
        return self._project_config.data_dir / self.csv_filename

    @property
    def bm_path(self):
        return self._project_config.data_dir / self.biomet_filename

    def check_measurements_to_keep(self, run_config):
        if run_config.obs_var not in self.measurements_to_keep:
            self.measurements_to_keep.append(run_config.obs_var)

        if run_config.filter_var not in self.measurements_to_keep:
            self.measurements_to_keep.append(run_config.filter_var)

    def __post_init__(self):
        self.vtk = self.measurements_to_keep
        self.qc_lvl = self.quality_level_to_keep
        self.zm = self.measurement_height

        self.D = len(self.driver_variables)  # number of driver variables


@dataclass
class LandCoverParams:
    _project_config: ProjectConfig

    dx: float
    dy: float

    land_cover_filename: str
    land_cover_names: List[str]
    land_cover_short_names: List[str] = None
    land_cover_groups: List[List[int]] = field(
        default_factory=lambda: [
            [0, 9],  # water
            [1, 2, 3, 4, 10],  # grass
            [5, 6, 7, 8, 11, 12, 13],
        ]  # vegetation
    )

    @property
    def land_cover_fn(self):
        return self._project_config.data_dir / self.land_cover_filename

    def __post_init__(self):
        # Calculate number of land cover groups:
        #   I_gtyp after land_cover_groups is initialized
        number_of_land_cover_groups: int = len(self.land_cover_groups)
        self.I_gtyp = number_of_land_cover_groups
        self.lt_grp = self.land_cover_groups


@dataclass
class FootprintParams:
    # spectral model parameters
    modes: list
    nz: int

    # domain padding width
    spectral_domain_padding_width: int = 0

    def __post_init__(self):
        self.pad_width = self.spectral_domain_padding_width


@dataclass
class InversionParams:
    regularization_parameter: float = 5e-2
    kernel_type: str = "RBF"  # 'RBF' or 'polynomial'
    gamma: float = 1.0  # for RBF

    def __post_init__(self):
        self.regularization_parameter = float(self.regularization_parameter)
        self.gamma = float(self.gamma)


@dataclass
class DiagnosticConfig:
    # output flags
    output_land_cover_mask: bool

    # debug plot flags
    debug_plot_stacked_land_covers: bool

    sample_size: int = 0


@dataclass
class RunConfig:
    """
    Configuration parameters for the run and orchestrator for all other data classes.
    """

    run_name: str

    observation_variable: str
    driver_variables_to_filter: str

    dataset: DatasetParams
    landcover: LandCoverParams
    footprint_model: FootprintParams
    diagnostics: DiagnosticConfig
    inversion: InversionParams

    def __post_init__(self):
        self.obs_var = self.observation_variable
        self.filter_var = self.driver_variables_to_filter


@dataclass
class GridParams:
    nx: int
    ny: int
    xmx: float
    ymx: float
    x: NDArray
    y: NDArray
    grid_src_row: int
    grid_src_col: int
    pad_width: int
    curr: NDArray  # helper attribute for "current" domain array

    measurement_point: tuple[int, int] = field(init=False)

    def __post_init__(self):
        self.measurement_point = (self.grid_src_col, self.grid_src_row)


@dataclass
class SimData:
    grid: GridParams
    land_cover_by_group: NDArray
    land_cover_mask_by_group: NDArray
    measurement_data: pd.DataFrame = field(default_factory=pd.DataFrame)

    N: int = 0  # number of time steps / measurements

    def __post_init__(self):
        self.N = len(self.measurement_data)


@dataclass
class GenerateSynthParams:
    run_name: str = "synth"
    random_seed: int = 42

    noise_amplitude: float = 0.05
    measurement_noise: float = 0.05
    quality_level_of_flux: int = 1
    ustar: float = 0.6
    time_frequency: str = "30min"

    PARmax: float = 1000.0
    Tamp: float = 12.0

    def __post_init__(self):
        self.noise_amp = self.measurement_noise
        self.qc_flx = self.quality_level_of_flux
        self.freq = self.time_frequency
