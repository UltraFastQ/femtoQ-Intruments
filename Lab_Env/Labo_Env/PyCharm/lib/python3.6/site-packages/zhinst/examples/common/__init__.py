"""
Zurich Instruments LabOne Python API Examples (for any instrument class).
"""

import zhinst.examples.common.example_autoranging_impedance
import zhinst.examples.common.example_connect
import zhinst.examples.common.example_connect_config
import zhinst.examples.common.example_data_acquisition_edge
import zhinst.examples.common.example_data_acquisition_edge_fft
import zhinst.examples.common.example_data_acquisition_grid
import zhinst.examples.common.example_data_acquisition_trackingedge
import zhinst.examples.common.example_pid_advisor_pll
import zhinst.examples.common.example_poll
import zhinst.examples.common.example_save_device_settings_simple
import zhinst.examples.common.example_save_device_settings_expert
import zhinst.examples.common.example_scope
import zhinst.examples.common.example_scope_segments
import zhinst.examples.common.example_sweeper

__all__ = ["example_autoranging_impedance",
           "example_connect",
           "example_connect_config",
           "example_data_acquisition_edge",
           "example_data_acquisition_edge_fft",
           "example_data_acquisition_grid",
           "example_data_acquisition_trackingedge",
           "example_pid_advisor_pll",
           "example_poll",
           "example_save_device_settings_expert",
           "example_save_device_settings_simple",
           "example_scope",
           "example_scope_segments",
           "example_sweeper"]

del zhinst
