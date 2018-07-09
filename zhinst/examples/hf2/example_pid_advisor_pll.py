"""
Zurich Instruments LabOne Python API Example

Demonstrate how to connect to a Zurich Instruments HF2 Lock-in Amplifier and use
the PID Advisor to set up an internal PLL control loop using ziDAQServer's
pidAdvisor Module.
"""

# Copyright 2017 Zurich Instruments AG

from __future__ import print_function
import time
import numpy as np
import zhinst.utils


def run_example(device_id, do_plot=False):
    """
    Run the example: Connect to a Zurich Instruments HF2 and obtain optimized P,
    I, and D parameters for an internal PLL loop using ziDAQServer's pidAdvisor
    module.

    Requirements:

      HF2 with the PLL Options.

      Hardware configuration: Connect signal output 1 to signal input 1 with a
        BNC cable.

    Arguments:

      device_id (str): The ID of the device to run the example with. For
        example, `dev1000` or `hf2-dev1000`.

      do_plot (bool, optional): Specify whether to plot the calculated PLL
        model response. Default is no plot output.

    Returns:

      result (dict): A dictionary containing the PID Advisor result.

    Raises:

      Exception: If the device is not discoverable from the API.

      Exception: If the PLL Option is not installed.
    """

    # The API level supported by this example. Note, the HF2 data server
    # only supports API Level 1.
    apilevel_example = 1
    # Call a zhinst utility function that returns:
    # - an API session `daq` in order to communicate with devices via the data server.
    # - the device ID string that specifies the device branch in the server's node hierarchy.
    # - the device's discovery properties.
    err_msg = "This example only supports HF2 Instruments with the PLL Option installed."
    (daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_example, required_devtype='HF2',
                                                           required_options=['PLL'], required_err_msg=err_msg)
    zhinst.utils.api_server_version_check(daq)

    # PID configuration.
    target_bw = 10e3              # Target bandwidth (Hz).

    # Used ony when the device type is HF2.
    pll_index = 0                 # PLL index.
    center_frequency = 1e6

    # Define configuration and configure the device.
    out_channel = 0
    osc_index = 1
    # Get the value of the instrument's default Signal Output mixer channel.
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    amplitude = 1.0

    # create a base configuration: disable all outputs, demods and scopes
    general_setting = [['/%s/demods/*/rate'       % device, False],
                       ['/%s/demods/*/trigger'    % device, False],
                       ['/%s/sigouts/*/enables/*' % device, False],
                       ['/%s/demods/*/enable'     % device, False],
                       ['/%s/scopes/*/enable'     % device, False]]
    daq.set(general_setting)

    # Now configure the settings relevant to this experiment
    exp_setting = [
        ['/%s/oscs/%d/freq'             % (device, osc_index), center_frequency],
        ['/%s/sigouts/%d/on'            % (device, out_channel), True],
        ['/%s/sigouts/%d/enables/%d'    % (device, out_channel, out_mixer_channel), True],
        ['/%s/sigouts/%d/range'         % (device, out_channel), 1.0],
        ['/%s/sigouts/%d/amplitudes/%d' % (device, out_channel, out_mixer_channel), amplitude]]
    daq.set(exp_setting)

    # Perform a global synchronisation between the device and the data server:
    # Ensure that the settings have taken effect on the device before starting the pidAdvisor.
    daq.sync()

    # set up PID Advisor
    pidAdvisor = daq.pidAdvisor()

    # Turn off auto-calc on param change. Enabled
    # auto calculation can be used to automatically
    # update response data based on user input.
    pidAdvisor.set('pidAdvisor/auto', False)
    pidAdvisor.set('pidAdvisor/device', device)
    pidAdvisor.set('pidAdvisor/pid/targetbw', target_bw)

    # PID advising mode (bit coded)
    # bit 0: optimize/tune P
    # bit 1: optimize/tune I
    # bit 2: optimize/tune D
    # Example: mode = 7: Optimize/tune PID
    pidAdvisor.set('pidAdvisor/pid/mode', 7)

    # PID index to use (first PLL of device: 0)
    pidAdvisor.set('pidAdvisor/index', pll_index)

    # DUT model
    # source = 1: Lowpass first order
    # source = 2: Lowpass second order
    # source = 3: Resonator frequency
    # source = 4: Internal PLL
    # source = 5: VCO
    # source = 6: Resonator amplitude
    dut_source = 4
    pidAdvisor.set('pidAdvisor/dut/source', dut_source)

    if dut_source == 4:
        # HF2: Since the PLL and PID are 2 separate hardware units on the device, we need to additionally specify that
        # the PID Advisor should model the HF2's PLL.
        pidAdvisor.set('pidAdvisor/pid/type', 'pll')
        # Note: The PID Advisor is appropriate for optimizing the HF2's PLL parameters (pidAdvisor/pid/type set to
        # 'pll') or the HF2's PID parameters (pidAdvisor/pid/type set to 'pid').

    # IO Delay of the feedback system describing the earliest response
    # for a step change. This parameter does not affect the shape of
    # the DUT transfer function
    pidAdvisor.set('pidAdvisor/dut/delay', 0.0)

    # Other DUT parameters (not required for the internal PLL model)
    # pidAdvisor.set('pidAdvisor/dut/gain', 1.0)
    # pidAdvisor.set('pidAdvisor/dut/bw', 1000)
    # pidAdvisor.set('pidAdvisor/dut/fcenter', 15e6)
    # pidAdvisor.set('pidAdvisor/dut/damping', 0.1)
    # pidAdvisor.set('pidAdvisor/dut/q', 10e3)

    # Start values for the PID optimization. Zero
    # values will imitate a guess. Other values can be
    # used as hints for the optimization process.
    pidAdvisor.set('pidAdvisor/pid/p', 0)
    pidAdvisor.set('pidAdvisor/pid/i', 0)
    pidAdvisor.set('pidAdvisor/pid/d', 0)
    pidAdvisor.set('pidAdvisor/calculate', 0)

    # Start the module thread
    pidAdvisor.execute()
    time.sleep(2.0)
    # Advise
    pidAdvisor.set('pidAdvisor/calculate', 1)
    print('Starting advising. Optimization process may run up to a minute...')
    reply = pidAdvisor.get('pidAdvisor/calculate')

    t_start = time.time()
    t_timeout = t_start + 90
    while reply['calculate'][0] == 1:
        time.sleep(0.1)
        reply = pidAdvisor.get('pidAdvisor/calculate')
        progress = pidAdvisor.progress()
        print("Advisor progress: {:.2%}.".format(progress[0]), end="\r")
        if time.time() > t_timeout:
            pidAdvisor.finish()
            raise Exception("PID advising failed due to timeout.")
    print("")
    print("Advice took {:0.1f} s.".format(time.time() - t_start))

    # Get all calculated parameters.
    result = pidAdvisor.get('pidAdvisor/*', True)
    # Check that the dictionary returned by poll contains the data that are needed.
    assert result, "pidAdvisor returned an empty data dictionary?"

    if result is not None:
        # Now copy the values from the PID Advisor to the device's PLL.
        pidAdvisor.set('pidAdvisor/todevice', 1)
        # Note: On HF2 devices the PLL is an additional hardware entity on the device (it is not combined on the device
        # with the PID), so we need to copy the parameters to the appropriate nodes in the PLLS device branch, not to
        # the PIDS branch.
        #
        # Let's have a look at the optimised gain parameters.
        p_advisor = result['/pid/p'][0]
        i_advisor = result['/pid/i'][0]
        d_advisor = result['/pid/d'][0]
        print("The pidAdvisor calculated the following gains, P:", p_advisor, "I:", i_advisor, "D:", d_advisor, ".")

    if do_plot:
        import matplotlib.pyplot as plt
        plt.close('all')
        bode_complex_data = result['/bode'][0]['x'] + 1j*result['/bode'][0]['y']
        bode_grid = result['/bode'][0]['grid']

        step_x = result['/step'][0]['x']
        step_grid = result['/step'][0]['grid']

        bw_advisor = result['/bw'][0]

        _, ax_list = plt.subplots(2, 1)

        ax_list[0].plot(bode_grid, 20*np.log10(np.abs(bode_complex_data)))
        ax_list[0].set_xscale('log')
        ax_list[0].grid(True)
        ax_list[0].set_title("Calculated model response for internal PLL with " +
                             "P = %0.0f, I = %0.0f,\n""D = %0.5f and bandwidth %0.0f kHz"
                             % (p_advisor, i_advisor, d_advisor, bw_advisor* 1e-3))
        ax_list[0].set_ylabel('Bode Gain (dB)')

        ax_list[1].plot(bode_grid, np.angle(bode_complex_data)/np.pi*180)
        ax_list[1].set_xscale('log')
        ax_list[1].grid(True)
        ax_list[1].set_xlabel('Frequency (Hz)')
        ax_list[1].set_ylabel('Bode Phase (deg)')

        _, ax = plt.subplots(1, 1)
        ax.plot(step_grid*1e6, step_x)
        ax.grid(True)
        ax.set_title("Calculated model response for internal PLL with " +
                     "P = %0.0f, I = %0.0f,\nD = %0.5f and bandwidth %0.0f kHz"
                     % (p_advisor, i_advisor, d_advisor, bw_advisor* 1e-3))
        ax.set_xlabel('Time (us)')
        ax.set_ylabel('Step Response')

        plt.draw()
        plt.show()

    return result
