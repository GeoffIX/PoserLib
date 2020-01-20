PoserUI:

This module implements Poser User Interface features currently missing from PoserPython.

PoserUI Constants:
PoserUserInterfaceVersion, debug, millimetresPerPNU, CircleOfConfusion, UnitScaleFactor, UnitScaleType, 
UseCompression, TestParmName
POSER_USER_INTERFACE_VERSION, UNIT_SCALE_FACTOR, UNIT_SCALE_TYPE, USE_COMPRESSION, PPM_HASKEYATFRAME,
PPM_ISCONTROLPROP (preference key strings)
AutoScales (list of Viewport scaling option names)
ResolutionScales (list of animation render scale presets)
VisibleHidden (list of visibility status names)
CameraModels (dict mapping codes to camera model names)
CameraNames (tuple of built-in camera internal names)
CameraParmCodes (list of poser constants for camera parameters)
CameraPerspectiveParm, CameraUnitScaleParm, CameraHyperFocusParm, CameraDepthOfFieldParm, CameraUnitScaleName,
CameraHyperFocusName, CameraCircleOfConfusionName, CameraFarFocusName, CameraDepthOfFieldName (parameter name strings)
UnitTypeName (list of unit names)
UnitTypeAbbreviation (list of unit abbreviations)
PoserPythonMethod (dict mapping method keys to methods when available)
NodeInputCodeName (dict mapping poser node input type codes to names)
ParmCodeName (dict mapping poser parameter type codes to names)
FloatSubTypeNames (dict mapping float subtypes to names)
ValueOpTypeNames (dict mapping poser value operation type codes to names)
SimpleValueOpTypeCodes (dict mapping simple poser value operation type codes to names)
ScaleAxis (dict mapping poser scale axis parameter type codes to names)
RotAxis (dict mapping poser rotation axis parameter type codes to names)
TransAxis (dict mapping poser translation axis parameter type codes to names)
ScaleParmCodes (list of poser scale parameter type code)
AnimSetNameFmt (format string for displaying AnimSet names)
AnimSetNameAttr (Attribute name to provide python access to AnimSet names not yet exposed)
AnimSetExtensionAttr (Attribute name for identifying file extension required by AnimSet)
CustomDataKeyDelimiter (Character used to delimit list of CustomData keys that have been defined, but not exposed)
CustomDataListKey (Key string for CustomData containing list of other customData keys used)
CustomDataFrameDelimiter (Character used to delimit frame number suffix from CustomData base key)
CustomDataPoseNameKey (Base Key string possibly suffixed with frame number to associate pose file name with frame)
CustomDataPoseNameFrameFmt (Format string to create properly constructed customData key and frame number combination)
Custom (namedtuple to simplify assignment of customData status flags)
compressedSuffixes (tuple of compressed file extension strings known to poser)
uncompressedSuffixes (tuple of uncompressed file extension strings known to poser)
sameSuffix (dict mapping compressed or uncompressed to uncompressed file extensions)
otherSuffix (dict mapping uncompressed to compressed and compressed to uncompressed file extensions)
CameraSuffix, FaceSuffix, FigureSuffix, HairSuffix, HandSuffix, LightSuffix, PoseSuffix, PropSuffix (method indices)
LoadMethod (dict mapping uncompressed file extensions to poser library load file methods)
SaveMethod (dict mapping uncompressed file extensions to poser library save file methods)

PoserUI Methods:

def TestMethods( theParm=None ):
	"""
	This method determines whether Poser Python supports the HasKeyAtFrame parameter method.
	This method determines whether Poser Python supports the IsControlProp actor method.
	
	theParm:	An optionally supplied parameter to use for the method existence test
	"""

def ActorTypeName( theActor ):
	"""
	Return the actor type string which precedes the actor name in poser files.
	NOTE: Fallback detection methods for controlProp and groupingObject prop actors are used for environments where
	NOTE: specific identification methods have not been exposed to poser python as per version 11.0.6.33735
	
	theActor	: the actor whose type string is to be returned.
	"""

def GetCameraParm( theCamera, theParmCode, inherit=False ):
	"""
	Return the parameter of theCamera actor identified by its parameter code theParmCode or raise an exception.
	If no exception is raised, calls TestMethods with the camera parameter before returning it.
	For Depth model cameras, which inherit their orientation from a parent Light, if the optional inherit parameter
	is True, return the parent light's relevant parameter instead.
	
	theCamera	: the camera actor whose parameter is to be returned
	theParmCode	: the poser parameter code of the parameter to be returned
	inherit		: optional boolean defaulting to False, to return parent Light's parameter for Depth model cameras.
				: ignored for non-Depth cameras.
	"""

# Camera Model not exposed to Python yet. Simulate by testing parameter names.
def GetCameraModel( theCamera ):
	"""
	Return the camera model code for theCamera actor or None if the actor is not a camera.
	NOTE: Camera Model is not exposed to poser python as of version 11.0.6.33735, so simulate by testing parameter 
	NOTE: names.
	NOTE: "poser" cameras orbit their parent or the origin
	NOTE: "real" (dolly) cameras rotate about their own origin
	NOTE: "depth" cameras have no rotation capabilities and are typically parented to lights for shadow generation.
	
	theCamera	: the camera actor whose model code (0 = poser, 1 = real, 2 = depth) is to be returned.
	"""

def UserCreated( theCamera ):
	"""
	Return whether theCamera is userCreated, based on whether its InternalName() is not in the set of Poser standard
	camera names listed in the global CameraNames.
	NOTE: Returns int(1) if userCreated or int(0) if a standard poser or depth camera or not a camera actor.
	
	theCamera	: the camera actor whose userCreated status is to be returned.
	"""

def PNUToUnits(PNU):
	"""
	This method returns the current Poser UI units equivalent of PNU in Poser Native Units.
	
	PNU						: A length in Poser Native Units (1 PNU = 100 inches = 8.6 feet = 2.62128 metres)
	global UnitScaleFactor	: The current Poser UI unit selection read from the PoserPrefs file
	"""

def UnitsToPNU(units):
	"""
	This method returns the Poser Native Units equivalent of units in current Poser UI units.
	
	units					: A length in current Poser User Interface units.
	global UnitScaleFactor	: The current Poser UI unit selection read from the PoserPrefs file
	"""

def MillimetresToPNU(mm):
	"""
	This method returns the Poser Native Units equivalent of mm (in millimetres).
	
	mm							: A length in millimetres.
	global millimetresPerPNU	: The ratio 2621.28 millimetres per Poser Native Unit
	"""

def PNUToMillimetres(PNU):
	"""
	This method returns the millimetre equivalent of PNU (in Poser Native Units).
	
	PNU							: A length in Poser Native Units
	global millimetresPerPNU	: The ratio 2621.28 millimetres per Poser Native Unit
	"""

def HyperFocal(f, N, c):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# returned units are millimetres
	"""

def FStop(f, s, c):
	"""
	# f = focal length in millimetres
	# s = focus distance in millimetres
	# c = circle of confusion in millimetres
	# returned value is a scalar (unitless) representing the maximum DOF when focus distance = hyperfocus
	"""

def NearFocus(f, N, c, s):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# s = focus distance in millimetres
	# returned units are millimetres
	"""

def FarFocus(f, N, c, s):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# s = focus distance in millimetres
	# returned units are millimetres
	"""

def GetAnimSetNames():
	"""
	Return a list of names of animSets in the poser scene. AnimSet Names are not yet exposed to Python in 11.0.6.33735
	Names will either consist of the value of the 'Name' attribute of the animSet or the animSets() list index in the
	form 'AnimSet {}'.format(index)
	"""

def GetAnimSetAttribute( theAnimSetName, theAttribute ):
	"""
	Given an existing AnimSet name, return the value of the attribute with key theAttribute or None if not found.
	
	theAnimSetName	The name of the animSet whose attribute value is to be returned.
	theAttribute	The name of the attribute whose value is to be returned.
	"""

def GetAnimSetActorParms( theAnimSetName ):
	"""
	Given an existing AnimSet name, return an OrderedDict of actors and their parameters specified by the AnimSet.
	Return None if no such named animSet found
	NOTE: Though the animSet will naturally return a list of parameters, their actors must be subsequently determined.
	NOTE: We are making the assumption that all of the actors are either unparented props or belong to a single figure.
	NOTE: Should multiple figures be referenced by the animSet.Parameters() list, the dict returned should probably
	NOTE: be indexed by figure and actor, rather than just actor, so saving schemes can wrap the parameters.
	"""

def GetCustomDataPoseName( theFigure=None, theActor=None, theFrame=None, useLast=False, baseOnly=False, \
																			stripExt=False, useActor=False ):
	"""
	Check theFigure or theActor for customData 'PoseName#nn' keys matching the specified frame.
	If both theFigure and theActor are None, default to the currently selected scene actor.
	If useLast is set, return the customData 'PoseName' if 'PoseName#nn' is absent for that frame.
	Return the customData value (or None if not found) and which key was located.
	
	theFigure	The figure, if any selected for saving
	theActor	In the absence of a selected figure, the actor whose customData 'PoseName' is to be returned
	theFrame	The frame component of the 'PoseName#nn' customData key being searched for. If None, default to 
				the current scene frame
	useLast		Allows the 'PoseName' customData to be returned if frame specific version is absent
	baseOnly	Remove the path component and return only the basename
	stripExt	Remove the '.pz2' or other extension if True
	useActor	If theFigure is not None, try theActor before falling back to theFigure. (Single recursion)	
	"""

def StringSplitByNumbers(x):
	"""
	Regular expression sort key for numeric order sorting of digit sequences in alphanumeric strings
	Credit: Matt Connolly (http://code.activestate.com/recipes/users/4177092/)
	"""

def ListAllCustomData( theObject=None ):
	"""
	Print a list of all customData for theObject, or the entire scene, with frame references numerically sorted
	Excludes the CustomDataListKey itself, which is only there to provide missing customData lookup functionality
	
	theObject:	figure or actor type scene object. If None, report customData for the entire scene
	"""

def GetCustomDataKeys( theObject ):
	"""
	Given theObject, which may refer to either a figure or an actor, return a list of keys for which customData exists.
	
	theObject	the entity (figure or actor) whose list of customData keys are to be returned.
	"""

def SetCustomDataKeys( theObject, keys ):
	"""
	Given theObject, which may refer to either a figure or an actor, set the CustomDataListKey customData to the 
	concatenated, delimited list of keys specified.
	
	theObject	the entity (figure or actor) whose list of customData keys is to be set.
	keys		the list of keys to be concatenated and delimited then saved to CustomDataListKey.
	"""

def AddCustomData( theObject, key, value=None, storeWithPoses=0, storeWithMaterials=0 ):
	"""
	Given theObject, which may refer to either a figure or an actor, set its customData as specified.
	The key will be included in the CustomDataListKey value, delimited by CustomDataKeyDelimiter: ';'
	
	theObject			the entity (figure or actor) whose customData is to be set.
	key					the key whose customData value is to be set.
	value				the customData value associated with key.
	storeWithPoses		flag 0 or 1 indicating whether Poser will save the customData with poses.
	storeWithMaterials	flag 0 or 1 indicating whether Poser will save the customData with material poses.
	"""	
	
def UpdateCustomData( theObject, theData ):
	"""
	Given theObject, which may refer to either a figure or an actor, update its customData with theData.
	The value of the special key 'PoseName' is replicated with a key of the form 'PoseName#<n>', where <n> is the frame 
	number to which this pose is being applied, so multiple keyframes can be labelled with the name of the pose.
	All referenced keys will be included in the CustomDataListKey value, delimited by CustomDataKeyDelimiter: ';'
	
	theObject	the entity (figure or actor) whose customData is to be updated.
	theData		an OrderedDict() containing customData key, value pairs to be updated for the object.
				NOTE: Each value is a Custom namedtuple of the format ( storeWithPoses, storeWithMaterials, string )
	"""	
