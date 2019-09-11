# PoserPrefs.py
# (c) 2014-2018 GeoffIX (Geoff Hicks)
#
# This module provides standard handling for Poser Python Script preference files
# If a specified preference file does not exist at the normal location of Poser's own preferences,
# then Poser's preference file will be examined for compatible information, e.g. LAST_OPEN_SAVE_PATH
#
# v1.0	20140602	Initial module version
# v1.1	20140815	Allow initialisation without defined name and defaultLibrary parameters to
#					permit safe loading of Poser's own preferences alone without searching for
#					a non-existent preferences file. The Save method is prevented from overwriting
#					Poser's own preferences file.
# v1.2	20160526	Moved preference file path determination from Load() method to __init__() to allow Save() method
#					to correctly locate a new preference file on initial creation without requiring a Load() attempt.
#					Replaced self.path initialisation as empty list in __init__() with correct path as described above.
# v1.3	20180110	Included USE_COMPRESSION as no current exposure in Poser Python API in 11.1.0.34764
# v1.4	20190911	Protect path operations from empty, uninitialised preferences.
#					Initial Python 3 compatibility replacement of print statement with function.
#					Account for print statements with trailing comma by print( "...", end = " " ) to suppress newline
###############################################################################################
from __future__ import print_function

poserPrefsVersion = "1.4"
debug = False

POSER_PREFS_VERSION = "POSERPREFS_VERSION"
POSER_VERSION = "POSER_VERSION"
LAST_OPEN_SAVE_PATH = "LAST_OPEN_SAVE_PATH"
USE_COMPRESSION = "USE_COMPRESSION"
POSER_PREFS = "Poser Prefs"
GENERAL_FORMAT = '{} {}\n'
PATH_FORMAT = '{} "{}"\n'
VERSION_FORMAT = '{:0g}'
LIBRARY_PATH = [ "Runtime", "Libraries" ]

import os
import string
import collections
import poser

class Preferences:
	'Poser Python standard preference file handling'
	
	def __init__(self, name=None, defaultLibrary=None):
		"""
		Define preference file path attributes.
		name			: The name of the preference file. E.g. 'SaveAnimSet Prefs'
						: Defaults to 'Poser Prefs' if unspecified and Save() method will be disabled.
		defaultLibrary	: e.g. 'Pose' ==> Runtime:Libraries:Pose
		
		path			: List of os directory path elements
		file			: Preference file handle
		preferences		: An OrderedDict of preference keys and values. Initialise the keys before calling Load()
						: Preference keys always saved are POSERPREFS_VERSION and POSER_VERSION
						: Preference key LAST_OPEN_SAVE_PATH will be sought in Poser Prefs file if not found
		"""
		# Determine preference file location (Previously initialised invalidly as an empty list)
		try:
			self.path = poser.PrefsLocation()
		except:
			self.path = LegacyPrefsLocation()
		self.name = name
		self.library = defaultLibrary
		self.file = None
		self.preferences = collections.OrderedDict( [ \
										( POSER_PREFS_VERSION, poserPrefsVersion ), \
										( POSER_VERSION, VERSION_FORMAT.format( float ( poser.Version() ) ) ) ] )
	
	def UseDefaultLibrary(self, preferenceKey):
		"""
		This method for path preferences will determine whether a path lies within the :Runtime:Libraries
		hierarchy and if not, set the path to the defined defaultLibrary for the instance
		"""
		path = self.preferences[ preferenceKey ]
		if debug:
			print( "Testing hierarchy of {} preference: '{}'".format ( preferenceKey, path ) )
		if string.find(string.lower(path), "runtime") < 0 or string.find(string.lower(path), "libraries") < 0:
			if debug:
				print( "{} preference: '{}' is outside Runtime Libraries,".format( preferenceKey, path ), end = " " )
			try:
				pathList = [ poser.ContentRootLocation() ]
			except:
				pathList = [ os.path.dirname( poser.AppLocation() ) ]
			pathList.extend( LIBRARY_PATH )
			if self.library: # Protect os.path.join from None, or empty folder names
				pathList.extend( [ self.library ] )
			path = os.path.join( *pathList )
			if debug:
				print( "using '{}'.".format( path ) )
			self.preferences[ preferenceKey ] = path
	
	def SetVersions(self, versionKey, versionValue):
		"""
		This method sets the version preferences in the OrderedDict to the versions of the currently executing
		Poser application and python scripts and modules. Do this before saving preferences to override version
		info loaded from an old preference file .
		"""
		self.preferences[ POSER_VERSION ] = VERSION_FORMAT.format( float( poser.Version() ) )
		self.preferences[ POSER_PREFS_VERSION ] = poserPrefsVersion
		self.preferences[ versionKey ] = versionValue
	
	def Save(self):
		"""
		This method will write the preferences OrderedDict to the specified self.path and self.name file,
		overwriting any existing preferences. Take care to parse the loaded preferences and purge any unwanted
		ones in case the entire poser preferences file was loaded in the absence of the specified file.
		If self.name was omitted on initialisation, Save will do nothing to avoid overwriting Poser's prefs.
		"""
		if self.name is None:
			if debug:
				print( "Save disabled for unspecified preferences file." )
		else:
			self.file = open(os.path.join( self.path, self.name ), "wt") # Overwrite existing preferences
			for pref in self.preferences.keys():
				if isinstance( self.preferences[ pref ], basestring ): # Double quote strings
					self.file.write( PATH_FORMAT.format( pref, self.preferences[ pref ] ) )
					if debug:
						print( "basestring preference {} : {}".format( pref, self.preferences[ pref ] ) )
				else:
					self.file.write( GENERAL_FORMAT.format( pref, self.preferences[ pref ] ) )
					if debug:
						print( "general preference {} : {}".format( pref, self.preferences[ pref ] ) )
			self.file.close()
	
	def LegacyPrefsLocation():
		"""
		Poser Pro 2014 defines poser.PrefsLocation().
		This function returns the preference path for earlier Poser versions.
		"""
		prefs6Dir = [ "Runtime", "prefs" ]
		prefs7Dir = [ "~", "Library", "Preferences", "Poser 7" ]
		prefs8Dir = [ "~", "Library", "Preferences", "Poser", "8.0" ]
		prefsProDir = [ "~", "Library", "Preferences", "Poser Pro" ]
		prefsPro2010Dir = [ "~", "Library", "Preferences", "Poser Pro", "2.0" ]
		prefs9Dir = [ "~", "Library", "Preferences", "Poser", "9" ]
		prefsPro2012Dir = [ "~", "Library", "Preferences", "Poser Pro", "9" ]
		# prefsPro2014Dir = [ "~", "Library", "Application Support", "Poser Pro", "10" ]
		# as returned by poser.PrefsLocation()
		
		poserDir = [ os.path.dirname( poser.AppLocation() ) ]
		poserApp = os.path.basename( poser.AppLocation() )
		ver = poser.Version()
		if debug:
			print( "Poser Directory: ", poserDir )
			print( "Poser Application: ", poserApp )
			print( "Poser Version: ", ver )
		verIndex = string.rfind(ver, '.')
		proIndex = string.rfind(poserApp, 'Pro')
		if debug:
			print( "Pro Index: ", proIndex )
		if ver[:verIndex] == "9":
			if proIndex > 0:
				prefsDir = prefsPro2012Dir
			else:
				prefsDir = prefs9Dir
		elif ver[:verIndex] == "8":
			if proIndex > 0:
				prefsDir = prefsPro2010Dir
			else:
				prefsDir = prefs8Dir
		elif ver[:verIndex] == "7":
			if proIndex > 0:
				prefsDir = prefsProDir
			else:
				prefsDir = prefs7Dir
		else:
			prefsDir = poserDir.extend( prefs6Dir )
		return os.path.expanduser( os.path.join( *prefsDir ) )

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
		if loadExtra is None:
			loadExtra = False
		# Preserve list of required preference keys in case we load Posers' preference file
		initialKeys = self.preferences.keys()
		
		# Moved preference file path determination to __init__() method.
		if self.name is None: # Default to Poser Prefs file.
			prefFileName = os.path.join( self.path, POSER_PREFS )
		else:
			prefFileName = os.path.join( self.path, self.name )
		if debug:
			print( "Prefs Path: {}\nPrefs File: {}".format( self.path, prefFileName ) )
		
		# Open preference file
		try:
			self.file = open(prefFileName, "rt")
		except: # No prefFile, use Poser Prefs
			if debug:
				print( "No '{}' file found,".format( prefFileName ) )
			prefFileName = os.path.join( self.path, POSER_PREFS )
			if debug:
				print( "loading '{}'.".format( prefFileName ) )
			try:
				self.file = open(prefFileName, "rt")
			except: # No Poser Prefs
				if debug:
					print( "No '{}' file found,".format(  prefFileName ) )
		if self.file != None:
			# Read preferences
			trans = string.maketrans(os.path.sep, os.path.sep)
			while 1:
				lines = self.file.readlines(100000)
				if not lines:
					break
				for line in lines:
					if debug:
						print( "Read line {}".format( line ), end = " " )
					part = line.split() # Space delimited
					if loadExtra or part[0] in initialKeys:
						prefValue = ' '.join(part[1:]) # First split part is key, the rest is value
						self.preferences[ part[0] ] = prefValue.translate(trans, '"')
			self.file.close()
			
#"""