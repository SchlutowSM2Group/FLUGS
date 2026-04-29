"""Variable label management from metadata."""

import re
import tomli


class LabelManager:
    """Manages variable labels and formatting from metadata file."""

    def __init__(self, metadata_file):
        """Initialize label manager from TOML metadata file.

        Parameters
        ----------
        metadata_file : str or Path
            Path to TOML file containing variable metadata.
        """
        with open(metadata_file, "rb") as f:
            var_meta = tomli.load(f)["variables"]
        self.var_meta = var_meta

    def _strip_suffix(self, var_name):
        """Strip sensor/tower suffixes like _1_1_1 from variable names.

        Parameters
        ----------
        var_name : str
            Variable name potentially with numeric suffix.

        Returns
        -------
        str
            Base variable name without trailing _digit patterns.
        """
        base_name = re.sub(r"(_\d+)+$", "", var_name)
        return base_name

    def get_label(self, var_name):
        """Get formatted label for variable from metadata.

        Tries full variable name first, then falls back to stripped version
        (without sensor/tower suffixes). Returns original name if not found.

        Parameters
        ----------
        var_name : str
            Variable name to look up.

        Returns
        -------
        str
            Formatted label string with units (e.g., "Air Temperature [°C]").
        """
        # Try full name first
        if var_name in self.var_meta:
            meta = self.var_meta[var_name]
            if meta["unit"]:
                return f"{meta['long_name']} [{meta['unit']}]"
            else:
                return meta["long_name"]

        # Try with stripped suffix
        base_name = self._strip_suffix(var_name)
        if base_name != var_name and base_name in self.var_meta:
            meta = self.var_meta[base_name]
            if meta["unit"]:
                return f"{meta['long_name']} [{meta['unit']}]"
            else:
                return meta["long_name"]

        # Return original name if not found
        return var_name
