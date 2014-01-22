#!/usr/bin/evn python
#
# Configuration file management

import os.path
import threading
import logging

from screener.lib.util import synchronized

CONFIG_ACCESS_LOCK = threading.RLock()


# Configuration data stored as a dict
config_dict = {}

# Configuration filename
config_filename = None

# -- Options classes

import sys
import ConfigParser

class ConfigParserWithComments(ConfigParser.ConfigParser):

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % ConfigParser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                self._write_item(fp, key, value)
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value_obj) in self._sections[section].items():
                self._write_item(fp, key, value_obj)
                
            fp.write("\n")

    def _write_item(self, fp, key, value_obj):
        fp.write("# %s\n" % (value_obj.get_description(),))
        if value_obj.is_default():
            fp.write("#%s = %s\n\n" % (key, str(value_obj()).replace('\n', '\n\t')))
        else:
            fp.write("%s = %s\n\n" % (key, str(value_obj()).replace('\n', '\n\t')))

class Option(object):
    """
    Base Option class for defining an option within the application.
    """

    def __init__(self, section, keyword, default_val=None, add=True, description = ''):
        """
        section : single option section or comma-separated list of sections
        a list will be a hierarchy: "foo, bar" --> [foo][[bar]]
        keyword     : keyword in the (last) section
        default_val : value returned when no value has been set
        add         : should the config be added as a configurable option
        """
        self.__sections = section.split(',')
        self.__keyword = keyword
        self.__default_val = default_val
        self.__value = None
        self.__callback = None
        self.__add = add
        self.__description = description

        # Add to the config dictionary
        global config_dict
        anchor = config_dict
        for section in self.__sections:
            if section not in anchor:
                anchor[section] = {}
            anchor = anchor[section]
        anchor[keyword] = self

    def __call__(self):
        """
        Call get() replacement
        """
        return self.get()

    def get_description(self):
        """
        Retrieve value field
        """
        if self.__description == '':
            return 'Please Add a description for the following field'
        else:
            return str(self.__description)
        
    def get_string(self):
        """
        Retrieve value field
        """
        if self.__value != None:
            return str(self.__value)
        else:
            return str(self.__default_val)
    
    def get(self):
        """
        Retrieve value field
        """
        if self.__value != None:
            return self.__value
        else:
            return self.__default_val
        
    def is_default(self):
        return self.__value == None

    def add(self):
        """
        Retrieve value field
        """
        return self.__add

    def get_dict(self, safe=False):
        """
        Return value a dictionary
        """
        return { self.__keyword : self.get() }

    def set_dict(self, dict):
        """
        Set value based on dictionary
        """
        try:
            return self.set(dict['value'])
        except KeyError:
            return False

    def __set(self, value):
        """
        Set new value, no validation
        """
        global modified
        if (value != None):
            if type(value) == type([]) or type(value) == type({}) or value != self.__value:
                self.__value = value
                modified = True
                if self.__callback:
                    self.__callback()
        return None

    def set(self, value):
        return self.__set(value)

    def get_default(self):
        return self.__default_val

    def reset(self):
        self.__value = None

    def callback(self, callback):
        """
        Set a callback function for when the value is updated
        """
        self.__callback = callback

    def ident(self):
        """
        Return section-list and keyword
        """
        return self.__sections, self.__keyword

    def __str__(self):
        return 'Option<%s, %s, %s>' % (self.__sections, self.__keyword, self.get())


class OptionStr(Option):
    """
    String option
    """
    def __init__(self, section, keyword, default_val='', validation=None, add=True, description = '', strip=True):
        """
        validation : a function that adds additional validation of the value
        strip      : strip whitespace from the value
        """
        super(OptionStr, self).__init__(section, keyword, default_val, add, description)
        self.__validation = validation
        self.__strip = strip

    def get_float(self):
        """
        Return value converted to a float, allowing KMGT notation
        """
        return float(self.get())

    def get_int(self):
        """
        Return value converted to an int, allowing KMGT notation
        """
        return int(self.get_float())

    def set(self, value):
        """
        Set stripped value
        """
        error = None
        if type(value) == type('') and self.__strip:
            value = value.strip()
        if self.__validation:
            error, val = self.__validation(value)
            self._Option__set(val)
        else:
            self._Option__set(value)
        return error


class OptionNum(Option):
    """
    Numeric option class, whether it is an int or float
    is determined by default value.
    min_val: the minimum value of the number
    max_val : the maximum value of the number
    validation : a function that adds additional validation of the value
    """
    def __init__(self, section, keyword, default_val=0, minval=None, maxval=None, validation=None, add=True, description = ''):
        super(OptionNum, self).__init__(section, keyword, default_val, add, description)
        self.__minval = minval
        self.__maxval = maxval
        self.__validation = validation
        self.__int = type(default_val) == type(0)

    def set(self, value):
        """
        Ensure the min and max range limits if set
        """
        if value != None:
            try:
                if self.__int:
                    value = int(value)
                else:
                    value = float(value)
            except ValueError:
                value = 0
            if self.__validation:
                error, val = self.__validation(value)
                self._Option__set(val)
            else:
                if (self.__maxval != None) and value > self.__maxval:
                    value = self.__maxval
                elif (self.__minval != None) and value < self.__minval:
                    value = self.__minval
                self._Option__set(value)
        return None


class OptionBool(Option):
    """
    Boolean option class
    """
    def __init__(self, section, keyword, default_val=False, add=True, description = ''):
        super(OptionBool, self).__init__(section, keyword, bool(default_val), add, description)
    
    def set(self, value):
        if value is None:
            value = False
        try:
            if str(value).upper() in ["TRUE","YES","1"]:
                self._Option__set(True)
            else:
                self._Option__set(False)
        except ValueError:
            self._Option__set(False)
        return None

_logging_levels = {
    'NOTSET': logging.NOTSET,
    'DEBUG': logging.DEBUG,
    'AUDIT': getattr(logging, 'AUDIT', 25),
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}
class OptionLogLevel(Option):
    """
    LogLevel option class
    """
    def set(self, value):
        if value is None:
            value = logging.NOTSET
        val = str(value).upper()
        if val in _logging_levels.keys():
            self._Option__set(_logging_levels[val])
        else:
            intval = int(value)
            if intval in _logging_levels.values():
                self._Option__set(intval)
        return None


# -- End of options classes


@synchronized(CONFIG_ACCESS_LOCK)
def read(path):
    """
    Reads from a config file at 'path'.
    This function is synchronized with save() to prevent
    concurrency issues.
    """
    global config_dict, config_filename
    # Check whether the file exists
    # import pdb
    # pdb.set_trace()
    config_filename = path
    if not os.path.exists(path):
        try:
            # Create the file is none exists
            with open(path, 'w') as f:
                print 'Creating new config file', path
                print os.path.dirname(__file__)
                conf_file = ConfigParserWithComments()
                conf_file.read(path)
                save()
                pass
        except IOError, e:
                logging.error('Unable to create new config file %s' % path)
                raise e
    try:
        conf_file = ConfigParserWithComments()
        conf_file.read(path)

        for section in conf_file.sections():
            for option in conf_file.options(section):
                try:
                    config_dict[section][option].set(conf_file.get(section, option))
                except KeyError:
                    logging.warning('Unknown config option [%s]%s' % (section, option))
    except IOError:
        logging.error('Unable to open %s config file' % path)


@synchronized(CONFIG_ACCESS_LOCK)
def save():
    """
    Writes the interal config state to a config file.
    This function is synchronized with save() to prevent
    concurrency issues.
    """
    global config_dict, config_filename
    conf_file = ConfigParserWithComments()
    for section, options in config_dict.items():
        if not conf_file.has_section(section):
            conf_file.add_section(section)
        for option, option_value in options.items():
            if option_value.add():
                conf_file.set(section, option, option_value)
                
    # Write the config file    
    with open(config_filename, 'w') as f:
        conf_file.write(f)
        
def summary():
    """
    Returns a snapshot dict of the current config values
    """
    output = {}
    for section, options in config_dict.items():
        output[section] = {}
        for option, option_value in options.items():
            output[section][option] = option_value()
    return output

# Testing code for configs
if __name__ == '__main__':
    conf = read('./test.cfg')
    print conf._sections
    print conf.sections()
    print conf.options('tms')
    print conf.get('tms', 'ingest')
    for k, v in conf._sections.items():
        print k
        for k1, v1 in v.items():
            print k1, v1, type(v1)