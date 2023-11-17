PoserPrefs:

This module provides standard handling for Poser Python Script preference files
If a specified preference file does not exist at the normal location of Poser's own preferences,
then Poser's preference file will be examined for compatible information, e.g. LAST_OPEN_SAVE_PATH
Note that methods will not allow Poser's own preferences to be overridden on save.

PoserPrefs Constants:
__version__, poserPrefsVersion, debug, POSER_PREFS_VERSION, POSER_VERSION, LAST_OPEN_SAVE_PATH, LIB_ITEMS_SERVER_SORT, 
USE_COMPRESSION, POSER_PREFS, GENERAL_FORMAT, PATH_FORMAT, VERSION_FORMAT, LIBRARY_PATH

PoserPrefs Methods:

class Preferences:
	'Poser Python standard preference file handling'
	
	def __init__(self, name=None, defaultLibrary=None, path=None):
		"""
		Define preference file path attributes.
		name			: The name of the preference file. E.g. 'SaveAnimSet Prefs'
						: Defaults to 'Poser Prefs' if unspecified and Save() method will be disabled.
		defaultLibrary	: e.g. 'Pose' ==> Runtime:Libraries:Pose
		path			: The location of the preference file. 
						: Defaults to the location of Poser's preferences if unspecified.
						: path kwarg will only be used if name kwarg is defined.
		
		file			: Preference file handle
		preferences		: An OrderedDict of preference keys and values. Initialise the keys before calling Load()
						: Preference keys always saved are POSERPREFS_VERSION and POSER_VERSION
						: Preference key LAST_OPEN_SAVE_PATH will be sought in Poser Prefs file if not found
		json			: A list (initially empty) of keys whose values are JSON encoded.
		"""
		# Determine preference file location (Previously initialised invalidly as an empty list)
	
	def UseDefaultLibrary(self, preferenceKey):
		"""
		This method for path preferences will determine whether a path lies within the :Runtime:Libraries
		hierarchy and if not, set the path to the defined defaultLibrary for the instance
		"""
	
	def SetVersions(self, versionKey, versionValue):
		"""
		This method sets the version preferences in the OrderedDict to the versions of the currently executing
		Poser application and python scripts and modules. Do this before saving preferences to override version
		info loaded from an old preference file .
		"""
	
	def Save(self):
		"""
		This method will write the preferences OrderedDict to the specified self.path and self.name file,
		overwriting any existing preferences. Take care to parse the loaded preferences and purge any unwanted
		ones in case the entire poser preferences file was loaded in the absence of the specified file.
		If self.name was omitted on initialisation, Save will do nothing to avoid overwriting Poser's prefs.
		"""
	
	def LegacyPrefsLocation():
		"""
		Poser Pro 2014 defines poser.PrefsLocation().
		This function returns the preference path for earlier Poser versions.
		"""

	def Load(self, loadExtra=None):
		"""
		This method will determine where the Poser preference files are located and attempt to load
		preference key values into the preferences dict from either the specified file or the Poser Prefs file.
		The path attribute will contain the specified preference file name appended to the path with 
		OS appropriate username, link and navigation expansion and separators.
		Note that preference version information loaded from an old file may not match current executable 
		versions, so call SetVersions before re-saving preferences.
		
		loadExtra (optional boolean)	: Permit loading of additional preferences from file beyond existing keys.
		"""

PoserPrefs Usage:
For a python script arbitrarily called myScript.py, the following code might be used to set up preferences handling.

# Some preference constants
myScriptPrefs = 'myScriptPrefs.ini' # The preference file name
version = '1.0' # A version number preference string
debug = True # A boolean preference
verbosity = 0 # An integer preference

# The preference key strings that will appear in the preference file preceding each of the above values
MY_SCRIPT_VERSION = 'MY_SCRIPT_VERSION'
MY_SCRIPT_DEBUG = 'MY_SCRIPT_DEBUG'
MY_SCRIPT_VERBOSE = 'MY_SCRIPT_VERBOSE'

from PoserLib import PoserPrefs as prefs

# Instantiate myScript preferences
myPrefsPath = 'Somewhere over the rainbow' # This should be a real location different from where Poser's prefs live
prefs = PoserPrefs.Preferences( myScriptPrefs, path = myPrefsPath )

# Initialise preferences OrderedDict with what we're looking for.
prefs.preferences[ MY_SCRIPT_VERSION ] = version
prefs.preferences[ MY_SCRIPT_DEBUG ] = debug
prefs.preferences[ MY_SCRIPT_VERBOSE ] = verbosity
prefs.preferences[ PoserPrefs.LAST_OPEN_SAVE_PATH ] = '' # Path string from Poser's own preference file

# Load preferences
prefs.Load( True ) # Allow extraneous preferences possibly loaded from Poser's prefs file.
prefs.UseDefaultLibrary( PoserPrefs.LAST_OPEN_SAVE_PATH ) # Use default if outside :Runtime:Libraries
# Convert boolean preference strings to bool as bool('False') != False
for pref in [ MY_SCRIPT_DEBUG ]: # Just list the boolean preferences
	if not isinstance( prefs.preferences[ pref ], bool ): # Compare with 'False' for boolean value
		prefs.preferences[ pref ] = not ( prefs.preferences[ pref ] == 'False' )
# Now we can parse any boolean preferences to the local variables
debug = bool( prefs.preferences[ MY_SCRIPT_DEBUG ] ) or debug # Script enable overrides pref disable
verbosity = int( prefs.preferences[ MY_SCRIPT_VERBOSE ] )

...

# When saving myScript preferences, use this logic
prefs.SetVersions( MY_SCRIPT_VERSION, version ) # Reset preference versions possibly loaded from file
prefs.preferences[ PoserPrefs.LAST_OPEN_SAVE_PATH ] = 'Another fine mess' # This still goes in MyScript's prefs file.
prefs.Save() # Overwrite the preference file

