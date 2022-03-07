#!/usr/bin python
# -*- coding: utf-8 -*-
"""Provide GCSError defines and GCSError exception class."""
# too many lines in module pylint: disable=C0302
# line too long pylint: disable=C0301

from logging import debug
import json
import os

from ..pierror_base import PIErrorBase

__signature__ = 0x41a380289975912b8a00ee111a8c47f1

# /*!
#  * \brief Structure of an UMF error.
#  * \- RSD:   		Reserved bit
#  * \- FGroup ID: 	Functional Group ID
#  * \- Error Class:  Config or Processing error
#  * \- Error Code:   The error code
#  *  _______________________________________________________________________________________________________________________________
#  * |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#  * |             Reserve           |                  FunctionGroup                |   ErrClass    |           ErrorID             |
#  * |___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|
#  *
#  */

# error definition begin  ## DO NOT MODIFY THIS LINE!!!
E0_PI_ERROR_NO_ERROR = 0
E8961_PI_ERROR_CMD_NUMBER_OF_ARGUMENTS = 8961
E8962_PI_ERROR_CMD_UNKNOWN_COMMAND = 8962
E8965_PI_ERROR_CMD_COMMAND_LEVEL_TOO_LOW_FOR_COMMAND_ACCESS = 8965
E8970_PI_ERROR_CMD_INVALID_PWD = 8970
E8972_PI_ERROR_CMD_UNKNOWN_SECTION_COMMAND = 8972
E9582_PI_ERROR_CMD_STOP = 9582
E16385_PI_ERROR_PARAM_WRONG_DATA_TYPE = 16385
E17154_PI_ERROR_PARAM_UNKNOWN_PARAMETER_ID = 17154
E17157_PI_ERROR_PARAM_COMMAND_LEVEL_TOO_LOW_FOR_PARAMETER_ACCESS = 17157
E17162_PI_ERROR_PARAM_INVALID_VALUE = 17162
E17163_PI_ERROR_PARAM_WRONG_PARAMETER_TYPE = 17163
E17192_PI_ERROR_PARAM_VALUE_OUT_OF_RANGE = 17192
E21250_PI_ERROR_MOTION_UNKNOWN_AXIS_ID = 21250
E21255_PI_ERROR_MOTION_ON_LIMIT_SWITCH = 21255
E21258_PI_ERROR_MOTION_INVALID_MODE_OF_OPERATION = 21258
E21259_PI_ERROR_MOTION_MOVE_WITHOUT_REF = 21259
E21260_PI_ERROR_MOTION_INVALID_AXIS_STATE = 21260
E21288_PI_ERROR_MOTION_TARGET_OUT_OF_RANGE = 21288
E21448_PI_ERROR_MOTION_AXIS_DISABLED = 21448
E21449_PI_ERROR_MOTION_FAULT_REACTION_ACTIVE = 21449
E21767_PI_ERROR_MOTION_LIMIT_SWITCH_ACTIVATED = 21767
E21800_PI_ERROR_MOTION_OVER_CURRENT_PROTECTION = 21800
E21801_PI_ERROR_MOTION_POSITION_ERROR_TOO_LARGE = 21801
E21870_PI_ERROR_MOTION_STOP = 21870
E24583_PI_ERROR_RECORDER_MAX_DATA_RECORDER_NUMBER_REACHED = 24583
E24596_PI_ERROR_RECORDER_ALREADY_REGISTERED = 24596
E25345_PI_ERROR_RECORDER_WRONG_FORMAT = 25345
E25346_PI_ERROR_RECORDER_UNKNOWN_RECORDER_ID = 25346
E25354_PI_ERROR_RECORDER_NOT_IN_CONFIG_MODE = 25354
E25356_PI_ERROR_RECORDER_WRONG_TRIGGER_ID = 25356
E25358_PI_ERROR_RECORDER_WRONG_STARTPOINT = 25358
E25359_PI_ERROR_RECORDER_WRONG_NUMPOINT = 25359
E25364_PI_ERROR_RECORDER_ALREADY_RUNNING = 25364
E25384_PI_ERROR_RECORDER_TRACE_DOES_NOT_EXIST = 25384
E25414_PI_ERROR_RECORDER_NOT_ENOUGH_RECORDED_DATA = 25414
E25415_PI_ERROR_RECORDER_TRACES_NOT_CONFIGURED = 25415
E33380_PI_ERROR_COM_COMMUNICATION_ERROR = 33380
E33538_PI_ERROR_COM_FW_INDEX_UNKNOWN = 33538
E33796_PI_ERROR_COM_TIMEOUT = 33796
E33803_PI_ERROR_COM_INVALID_SOCKET = 33803
E36865_PI_ERROR_SYS_WRONG_UNIT_ID_FORMAT = 36865
E36867_PI_ERROR_SYS_UNIT_NOT_INITIALIZED = 36867
E36871_PI_ERROR_SYS_MAX_CONNECTION_NUMBER_REACHED = 36871
E36874_PI_ERROR_SYS_CONNECTION_OUTPUT_WRONG_ARGUMENTS = 36874
E36875_PI_ERROR_SYS_CONNECTION_INPUT_WRONG_ARGUMENTS = 36875
E36877_PI_ERROR_SYS_WRONG_DEVICE_ID = 36877
E36878_PI_ERROR_SYS_WRONG_FUNCTION_ID = 36878
E36879_PI_ERROR_SYS_WRONG_PROXY_ID = 36879
E36904_PI_ERROR_SYS_CONNECTION_OUTPUT_INDEX_OUT_OF_RANGE = 36904
E36914_PI_ERROR_SYS_INTERFACE_REGISTRATION_FAILED = 36914
E36915_PI_ERROR_SYS_DEVICE_REGISTRATION_FAILED = 36915
E36916_PI_ERROR_SYS_PROXY_REGISTRATION_FAILED = 36916
E37140_PI_ERROR_SYS_INPUT_PORT_ALREADY_CONNECTED = 37140
E37141_PI_ERROR_SYS_UNIT_ALREADY_REGISTERED = 37141
E37180_PI_ERROR_SYS_CONNECTION_HAS_NO_INPUT = 37180
E37181_PI_ERROR_SYS_CONNECTION_HAS_NO_OUTPUT = 37181
E37183_PI_ERROR_SYS_CONNECTION_NOT_FOUND = 37183
E37184_PI_ERROR_SYS_INPUT_PORT_NOT_CONNECTED = 37184
E37446_PI_ERROR_SYS_DATA_CORRUPT = 37446
E37633_PI_ERROR_SYS_CMD_UNIT_TYPE_NOT_SUPPORTED = 37633
E37682_PI_ERROR_SYS_FW_UPDATE_ERROR = 37682
E37692_PI_ERROR_SYS_UNIT_NOT_FOUND = 37692
E37693_PI_ERROR_SYS_CUNIT_NOT_FOUND = 37693
E37694_PI_ERROR_SYS_FUNIT_NOT_FOUND = 37694
E37889_PI_ERROR_SYS_UNIT_TYPE_NOT_SUPPORTED = 37889
E37918_PI_ERROR_SYS_NOT_ENOUGH_MEMORY = 37918
E37938_PI_ERROR_SYS_FLASH_READ_FAILED = 37938
E37948_PI_ERROR_SYS_NO_DATA_AVAILABLE = 37948
E37988_PI_ERROR_SYS_FATAL_ERROR = 37988

# error definition end  ## DO NOT MODIFY THIS LINE!!!


PI_GCS21_ERRORS_ERRORS_DICT_KEY = 'errors'
PI_GCS21_ERRORS_MODULES_DICT_KEY = 'modules'
PI_GCS21_ERRORS_CLASSES_DICT_KEY = 'classes'
PI_GCS21_ERRORS_ID_KEY = 'id'
PI_GCS21_ERRORS_MODULE_KEY = 'module'
PI_GCS21_ERRORS_CLASS_KEY = 'class'
PI_GCS21_ERRORS_DESCRIPTION_KEY = 'description'
PI_GCS21_ERRORS_TYP_KEY = 'typ'
PI_GCS21_ERRORS_VALUE_KEY = 'value'

ERROR_FILE_PATH = os.path.dirname(__file__) + '/Error.json'
POSSIBLE_ERRORS = {}
with open(ERROR_FILE_PATH, 'r') as error_file:
    POSSIBLE_ERRORS = json.load(error_file)


class GCS21Error(PIErrorBase):
    """GCSError exception."""

    def __init__(self, value, message=''):
        """GCSError exception.
        :param value : Error value as integer.
        :param message : Optional message to show in exceptions string representation.
        """
        PIErrorBase.__init__(self, value, message)
        if isinstance(value, GCS21Error):
            self.err = value.err
        else:
            self.err = GCS21Error.get_error_dict(value)
            if self.err:
                self.msg = self.translate_error(self.err)

        debug('GCS21Error: %s', self.msg)

    @staticmethod
    def translate_error(value):
        """Return a readable error message of 'value'.
        :param value : Error value as integer or a gcs21 error dictionary.
        :return : Error message as string if 'value' was an integer else 'value' itself.
        """

        if not isinstance(value, (int, dict)):
            return value

        if isinstance(value, int):
            error_dict = GCS21Error.get_error_dict(value)
        else:
            error_dict = value

        try:
            msg = 'ERROR: ' + str(error_dict[PI_GCS21_ERRORS_VALUE_KEY]) + '\n'
            msg = msg + error_dict[PI_GCS21_ERRORS_MODULE_KEY][PI_GCS21_ERRORS_DESCRIPTION_KEY] + ' (' + str(
                error_dict[PI_GCS21_ERRORS_MODULE_KEY][PI_GCS21_ERRORS_ID_KEY]) + '): '
            msg = msg + error_dict[PI_GCS21_ERRORS_DESCRIPTION_KEY] + ' (' + str(
                error_dict[PI_GCS21_ERRORS_ID_KEY]) + ')\n'
            msg = msg + error_dict[PI_GCS21_ERRORS_CLASS_KEY][PI_GCS21_ERRORS_DESCRIPTION_KEY] + ' (' + str(
                error_dict[PI_GCS21_ERRORS_CLASS_KEY][PI_GCS21_ERRORS_ID_KEY]) + ')\n'
        except KeyError:
            if isinstance(value, int):
                module_id, error_class, error_id = GCS21Error.parse_errorcode(value)
                msg = 'ERROR: ' + str(value) + '\nUnknown error: module: ' + str(module_id) + ', class: ' + str(
                    error_class) + ', error: ' + str(error_id) + '\n'
            else:
                msg = 'ERROR: Unknown error\n'

        return msg

    @staticmethod
    def parse_errorcode(error_number):
        """
        parses a error code returnd by the controller into the mocule, class, and error number
        :param error_number: the error code
        :return: [moduel, class, error_number]
        """
        module_id = (error_number & 0x000fff000) >> 12
        error_class = (error_number & 0x00000f00) >> 8
        error_id = error_number & 0x000000ff

        return module_id, error_class, error_id

    @staticmethod
    def parse_to_errorcode(module_id, error_class, error_id):
        """
        parses module id, error class and error id to error number
        :param module_id: the error code
        :type module_id: int
        :param error_class: the error class
        :type error_class: int
        :param error_id: the error id
        :type error_id: int
        :return: error_number
        """
        error_number = ((module_id << 12) & 0x000fff000) | \
                       ((error_class << 8) & 0x00000f00) | \
                       (error_id & 0x000000ff)
        return error_number

    @staticmethod
    def get_error_dict(error_number):
        """
        gets the gcs21 error dictionary form the error number
        :param error_number:
        :return:
        """
        error_dict = {}
        module_id, error_class, error_id = GCS21Error.parse_errorcode(error_number)
        #    module_id = (error_number & 0xf800) >> 11
        #    error_class = (error_number & 0x0700) >> 8
        #    error_id = error_number & 0x00ff

        module_dict = {}
        for module in POSSIBLE_ERRORS[PI_GCS21_ERRORS_MODULES_DICT_KEY]:
            if POSSIBLE_ERRORS[PI_GCS21_ERRORS_MODULES_DICT_KEY][module][PI_GCS21_ERRORS_ID_KEY] == module_id:
                module_dict = POSSIBLE_ERRORS[PI_GCS21_ERRORS_MODULES_DICT_KEY][module]
                module_dict[PI_GCS21_ERRORS_TYP_KEY] = module

        classes_dict = {}
        for classe in POSSIBLE_ERRORS[PI_GCS21_ERRORS_CLASSES_DICT_KEY]:
            if POSSIBLE_ERRORS[PI_GCS21_ERRORS_CLASSES_DICT_KEY][classe][PI_GCS21_ERRORS_ID_KEY] == error_class:
                classes_dict = POSSIBLE_ERRORS[PI_GCS21_ERRORS_CLASSES_DICT_KEY][classe]
                classes_dict[PI_GCS21_ERRORS_TYP_KEY] = classe

        # Wrong hanging indentation before block (add 4 spaces).  pylint: disable = C0330
        for err in POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY]:
            if POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY][err][PI_GCS21_ERRORS_ID_KEY] == error_id and \
                    POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY][err][
                        PI_GCS21_ERRORS_CLASS_KEY] == classes_dict[PI_GCS21_ERRORS_TYP_KEY] and \
                    POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY][err][
                        PI_GCS21_ERRORS_MODULE_KEY] == module_dict[PI_GCS21_ERRORS_TYP_KEY]:
                error_dict = {PI_GCS21_ERRORS_TYP_KEY: err}
                error_dict[PI_GCS21_ERRORS_MODULE_KEY] = module_dict
                error_dict[PI_GCS21_ERRORS_CLASS_KEY] = classes_dict
                error_dict[PI_GCS21_ERRORS_ID_KEY] = POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY][err][
                    PI_GCS21_ERRORS_ID_KEY]
                error_dict[PI_GCS21_ERRORS_DESCRIPTION_KEY] = POSSIBLE_ERRORS[PI_GCS21_ERRORS_ERRORS_DICT_KEY][err][
                    PI_GCS21_ERRORS_DESCRIPTION_KEY]
                error_dict[PI_GCS21_ERRORS_VALUE_KEY] = error_number

        return error_dict
