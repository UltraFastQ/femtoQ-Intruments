"""Zurich Instruments LabOne Python API Example

Demonstrate how to connect to a Zurich Instruments Lock-in Amplifier and and
obtain scope data using ziDAQServer's synchronous poll command.

"""

# Copyright 2017 Zurich Instruments AG

from __future__ import print_function
import numpy as np
import zhinst.utils


def run_example(device_id, do_plot=False):
    """Run the example: Connect to a Zurich Instruments Lock-in Amplifier and
    obtain scope data using ziDAQServer's synchronous poll command.

    Requirements:

      MF or UHF Instrument (HF2 not supported)

      Hardware configuration: Connect signal output 1 to signal input 1 with a
        BNC cable.

    Arguments:

      device_id (str): The ID of the device to run the example with. For
        example, `dev2006` or `uhf-dev2006`.

      do_plot (bool, optional): Specify whether to plot the boxcar and inputpwa
        output. Default is no plot output.

    Returns:

      data (dict of numpy arrays): The dictionary as returned by poll containing
        the subscribed data.

    Raises:

      Exception: If the specified device is not an MF or UHF.

      RuntimeError: If the device is not "discoverable" from the API.

    See the "LabOne Programing Manual" for further help, available:
      - On Windows via the Start-Menu:
        Programs -> Zurich Instruments -> Documentation
      - On Linux in the LabOne .tar.gz archive in the "Documentation"
        sub-folder.

    """

    apilevel_example = 5  # The API level supported by this example.
    # Call a zhinst utility function that returns:
    # - an API session `daq` in order to communicate with devices via the data server.
    # - the device ID string that specifies the device branch in the server's node hierarchy.
    # - the device's discovery properties.
    # This example can't run with HF2 Instruments.
    required_devtype = r'UHF|MF'  # Regular expression of supported instruments.
    required_options = {}  # No special options required.
    required_err_msg = "This example is incompatible with HF2 Instruments: The " + \
                       "HF2 Data Server does not support API Levels > 1, which " + \
                       "is required to use the extended scope data structure. " + \
                       "For HF2, see the example zhinst.examples.hf2.example_scope."

    (daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_example,
                                                           required_devtype=required_devtype,
                                                           required_options=required_options,
                                                           required_err_msg=required_err_msg)
    zhinst.utils.api_server_version_check(daq)

    # Create a base instrument configuration: disable all outputs, demods and scopes.
    general_setting = [['/%s/sigouts/*/enables/*' % device, 0],
                       ['/%s/scopes/*/enable' % device, 0]]
    node_branches = daq.listNodes('/%s/' % device, 0)
    if 'DEMODS' in node_branches:
        general_setting.append(['/%s/demods/*/enable' % device, 0])
    daq.set(general_setting)
    # Perform a global synchronisation between the device and the data server:
    # Ensure that the settings have taken effect on the device before setting
    # the next configuration.
    daq.sync()

    # Now configure the instrument for this experiment. The following channels
    # and indices work on all device configurations. The values below may be
    # changed if the instrument has multiple input/output channels and/or either
    # the Multifrequency or Multidemodulator options installed.
    # Signal output mixer amplitude [V].
    amplitude = 0.500
    out_channel = 0
    # Get the value of the instrument's default Signal Output mixer channel.
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    in_channel = 1
    osc_index = 0
    scope_in_channel = 0  # scope input channel
    frequency = 7e4
    exp_setting = [
        # The output signal.
        ['/%s/sigouts/%d/on'             % (device, out_channel), 1],
        ['/%s/sigouts/%d/enables/%d'     % (device, out_channel, out_mixer_channel), 1],
        ['/%s/sigouts/%d/range'          % (device, out_channel), 1],
        ['/%s/sigouts/%d/amplitudes/%d'  % (device, out_channel, out_mixer_channel), amplitude],
        ['/%s/sigins/%d/imp50'           % (device, in_channel), 1],
        ['/%s/sigins/%d/ac'              % (device, in_channel), 0],
        ['/%s/sigins/%d/range'           % (device, in_channel), 2*amplitude],
        ['/%s/oscs/%d/freq'              % (device, osc_index), frequency]]
    if 'DEMODS' in node_branches:
        # NOTE we don't need any demodulator data for this example, but we need
        # to configure the frequency of the output signal on out_mixer_c.
        general_setting.append(['/%s/demods/%d/oscselect' % (device, out_mixer_channel), osc_index])
    daq.set(exp_setting)

    # Perform a global synchronisation between the device and the data server:
    # Ensure that the signal input and output configuration has taken effect
    # before calculating the signal input autorange.
    daq.sync()

    # Perform an automatic adjustment of the signal inputs range based on the
    # measured input signal's amplitude measured over approximately 100 ms.
    # This is important to obtain the best bit resolution on the signal inputs
    # of the measured signal in the scope.
    # zhinst.utils.sigin_autorange(daq, device, in_channel)

    # Now configure the scope via the /devx/scopes/0/ node tree branch.
    # 'length' : the length of the scope shot
    daq.setInt('/%s/scopes/0/length' % device, int(1.0e3))
    # 'channel' : select the scope channel(s) to enable.
    #  Bit-encoded as following:
    #   1 - enable scope channel 0
    #   2 - enable scope channel 1
    #   3 - enable both scope channels (requires DIG option)
    # NOTE we are only interested in one scope channel: scope_in_c and leave the
    # other channel unconfigured
    daq.setInt('/%s/scopes/0/channel' % device, 1 << in_channel)
    # 'channels/0/bwlimit' : bandwidth limit the scope data. Enabling bandwidth
    # limiting avoids antialiasing effects due to subsampling when the scope
    # sample rate is less than the input channel's sample rate.
    #  Bool:
    #   0 - do not bandwidth limit
    #   1 - bandwidth limit
    daq.setInt('/%s/scopes/0/channels/%d/bwlimit' % (device, scope_in_channel), 1)
    # 'channels/0/inputselect' : the input channel for the scope:
    #   0 - signal input 1
    #   1 - signal input 2
    #   2, 3 - trigger 1, 2 (front)
    #   8-9 - auxiliary inputs 1-2
    #   The following inputs are additionally available with the DIG option:
    #   10-11 - oscillator phase from demodulator 3-7
    #   16-23 - demodulator 0-7 x value
    #   32-39 - demodulator 0-7 y value
    #   48-55 - demodulator 0-7 R value
    #   64-71 - demodulator 0-7 Phi value
    #   80-83 - pid 0-3 out value
    #   96-97 - boxcar 0-1
    #   112-113 - cartesian arithmetic unit 0-1
    #   128-129 - polar arithmetic unit 0-1
    #   144-147 - pid 0-3 shift value
    daq.setInt('/%s/scopes/0/channels/%d/inputselect' % (device, scope_in_channel), in_channel)
    # 'time' : timescale of the wave, sets the sampling rate to 1.8GHz/2**time.
    #   0 - sets the sampling rate to 1.8 GHz
    #   1 - sets the sampling rate to 900 MHz
    #   ...
    #   16 - sets the samptling rate to 27.5 kHz
    daq.setInt('/%s/scopes/0/time' % device, 0)
    # 'single' : only get a single scope shot.
    #   0 - take continuous shots
    #   1 - take a single shot
    daq.setInt('/%s/scopes/0/single' % device, 0)
    # 'trigenable' : enable the scope's trigger (boolean).
    #   0 - take continuous shots
    #   1 - take a single shot
    daq.setInt('/%s/scopes/0/trigenable' % device, 0)

    # Perform a global synchronisation between the device and the data server:
    # Ensure that the settings have taken effect on the device before issuing the
    # ``poll`` command and clear the API's data buffers to remove any old data.
    daq.sync()

    # 'enable' : enable the scope
    daq.setInt('/%s/scopes/0/enable' % device, 1)

    # Unsubscribe from any streaming data
    daq.unsubscribe('*')

    # Perform a global synchronisation between the device and the data server:
    # Ensure that the settings have taken effect on the device before issuing the
    # ``poll`` command and clear the API's data buffers to remove any old data.
    daq.sync()

    # Subscribe to the scope's data.
    daq.subscribe('/%s/scopes/0/wave' % device)

    # First, poll data without triggering enabled.
    poll_length = 1.0  # [s]
    poll_timeout = 100  # [ms]
    poll_flags = 0
    poll_return_flat_dict = False
    data_no_trig = daq.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
    print(data_no_trig)
    # Disable the scope.
    daq.setInt('/%s/scopes/0/enable' % device, 0)

    # Now configure the scope's trigger to get aligned data
    # 'trigenable' : enable the scope's trigger (boolean).
    #   0 - take continuous shots
    #   1 - take a single shot
    daq.setInt('/%s/scopes/0/trigenable' % device, 1)

    # Specify the trigger channel, we choose the same as the scope input
    daq.setInt('/%s/scopes/0/trigchannel' % device, in_channel)

    # Trigger on rising edge?
    daq.setInt('/%s/scopes/0/trigrising' % device, 1)

    # Trigger on falling edge?
    daq.setInt('/%s/scopes/0/trigfalling' % device, 0)

    # Set the trigger threshold level.
    daq.setDouble('/%s/scopes/0/triglevel' % device, 0.00)

    # Set hysteresis triggering threshold to avoid triggering on noise
    # 'trighysteresis/mode' :
    #  0 - absolute, use an absolute value ('scopes/0/trighysteresis/absolute')
    #  1 - relative, use a relative value ('scopes/0trighysteresis/relative') of the trigchannel's input range
    #      (0.1=10%).
    daq.setDouble('/%s/scopes/0/trighysteresis/mode' % device, 1)
    daq.setDouble('/%s/scopes/0/trighysteresis/relative' % device, 0.1)  # 0.1=10%

    # Set the trigger hold-off mode of the scope. After recording a trigger event, this specifies when the scope should
    # become re-armed and ready to trigger, 'trigholdoffmode':
    #  0 - specify a hold-off time between triggers in seconds ('scopes/0/trigholdoff'),
    #  1 - specify a number of trigger events before re-arming the scope ready to trigger ('scopes/0/trigholdcount').
    daq.setInt('/%s/scopes/0/trigholdoffmode' % device, 0)
    daq.setDouble('/%s/scopes/0/trigholdoff' % device, 0.025)

    # Set trigdelay to 0.: Start recording from when the trigger is activated.
    daq.setDouble('/%s/scopes/0/trigdelay' % device, 0.0)

    # Disable trigger gating.
    daq.setInt('/%s/scopes/0/triggate/enable' % device, 0)

    # Disable segmented data recording.
    daq.setInt('/%s/scopes/0/segments/enable' % device, 0)

    # Perform a global synchronisation between the device and the data server:
    # Ensure that the settings have taken effect on the device before issuing the
    # ``poll`` command and clear the API's data buffers to remove any old data.
    daq.sync()

    # 'enable' : enable the scope.
    daq.setInt('/%s/scopes/0/enable' % device, 1)

    # Subscribe to the scope's data.
    daq.subscribe('/%s/scopes/0/wave' % device)

    data_with_trig = daq.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
    print(data_with_trig)
    # Disable the scope.
    daq.setInt('/%s/scopes/0/enable' % device, 0)

    # Unsubscribe from any streaming data.
    daq.unsubscribe('*')

    # Check the dictionary returned by poll contains the subscribed data. The
    # data returned is a dictionary with keys corresponding to the recorded
    # data's path in the node hierarchy
    assert data_no_trig, "poll returned an empty data dictionary, did you subscribe to any paths?"
    assert '/%s/scopes/0/wave' % device in data_no_trig
    assert data_with_trig, "poll returned an empty data dictionary, did you subscribe to any paths?"
    assert '/%s/scopes/0/wave' % device in data_with_trig

    if do_plot:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm

        def plot_scope_shots(scope_shots, scope_input_channel):
            """Helper function to plot scope shots after applying the channeloffset and
            channelscaling."""
            colors = cm.rainbow(np.linspace(0, 1, len(scope_shots)))
            for index, shot in enumerate(scope_shots):
                totalsamples = shot['totalsamples']
                t = np.linspace(0, shot['dt']*totalsamples, totalsamples)
                # Scale the scope data using ``channelscaling'' field of the
                # scope data structure to obtain physical values for the
                # recorded scope data.  Note: ``channeloffset'' will always be 0
                # unless channels/0/{limitlower,limitupper} have been changed -
                # these are unavailable without the DIG Option.
                wave = shot['channeloffset'][scope_input_channel] + \
                    shot['channelscaling'][scope_input_channel]*shot['wave'][:, scope_input_channel]
                if (not shot['flags']) and (len(wave) == totalsamples):
                    plt.plot(1e6*t, wave, color=colors[index])
            plt.draw()

        # Plot the scope data with triggering disabled.
        plt.clf()
        plt.subplot(2, 1, 1)
        plt.grid(True)
        scope_shots_no_trig = data_no_trig['/%s/scopes/0/wave' % device]
        plot_scope_shots(scope_shots_no_trig, scope_in_channel)
        plt.title('{} Scope Shots from {} (triggering disabled)'.format(len(scope_shots_no_trig), device))
        plt.ylabel('Amplitude [V]')
        print('Number of scope shots with triggering disabled: {}.'.format(len(scope_shots_no_trig)))

        # Plot the scope data with triggering enabled.
        plt.subplot(2, 1, 2)
        plt.grid(True)
        scope_shots_with_trig = data_with_trig['/%s/scopes/0/wave' % device]
        plot_scope_shots(scope_shots_with_trig, scope_in_channel)
        plt.title('{} Scope Shots from {} (triggering enabled)'.format(len(scope_shots_with_trig), device))
        plt.xlabel('t [us]')
        plt.ylabel('Amplitude [V]')
        plt.show()
        print('Number of scope shots with triggering enabled: {}.'.format(len(scope_shots_with_trig)))

    return (data_no_trig, data_with_trig)

run_example('dev2318', do_plot=True)
