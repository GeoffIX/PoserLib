# PoserUI.py
# (c) 2014-2019 GeoffIX (Geoff Hicks)
# 
# This module implements Poser User Interface features currently missing from PoserPython.
#
# v1.0	20141128	Initial version based on CameraToEyeTarget.py v1.17
# v1.1	20150123	Include poser file I/O constants and methods
# v1.2	20150721	Added ActorTypeName method. Change default string delimiter to single quote.
#					Added ScaleAxis, RotAxis & TransAxis dicts
#		20150803	Extracted TestMethods() from GetCameraParm and initialise PoserPythonMethod on import.
# v1.3	20151201	Poser 11 Universe actor has no parameters by default, so change assumption and create one
#					to allow testing of methods.
# v1.4	20160303	Create ScaleParmCodes list to detect scale parameters with conforming influence
# v1.5	20160714	Added IsControlProp() method to ActorTypeName().
# v1.6	20170622	Incorporate AnimSet and customData methods from SaveAnimSetOneFrame.py v1.13
#					Credit: Matt Connolly (http://code.activestate.com/recipes/users/4177092/) for StringSplitByNumbers
#					Include SaveMethod dispatcher dict for creating library icons based on file extension.
#					Added SaveDocument to SaveMethod dispatcher for .pz3 scene files
#					Added groupingObject to ActorTypeName() method by inspecting GeomFileName() of actor.
#					Added file suffix mapping dict from any dot-prefixed extension to its uncompressed equivalent.
#					Changed CameraModels to a dict and add None:'' key:value so GetCameraModel can return None for
#					non-camera actors without raising an exception.
#					Added CameraNames set and UserCreated() method to distinguish userCreated cameras from poser 
#					cameras by their InternalName().
#					Added camera actor apertureRatio, apertureBlades & apertureBladesRotation parameterTypeCodes.
# v1.7	20170712	Added protection for groupingObject GeomFileName() returning None and crashing os.path methods.
# v1.8	20170824	Added NodeInputCodeName.
# v1.9	20170916	Added orientationXYZ to ParmCodeName dict.
# v1.10	20180112	Exposed Poser Preference USE_COMPRESSION via PoserUI.UseCompression boolean int as not available to
#					python API as of Poser Pro 11.1.0.34764
#					Added compressedSuffixes.
# v1.11	20180604	Fixed compressed suffix of .mt5 to .mz5 (not .mtz)
# v1.12	20180830	Added boolean flag 'Inherit' (default=False) to GetCameraParm() to allow the return of inherited
#					rotation parameters from the Light parent of depth cameras. 
# v1.13	20190402	Added UpdateCustomData() method to manage custom data for figures and actors by maintaining a
#					delimited list of customData keys as a separate CustomDataListKey value.
# v1.14	20190904	Added otherSuffix dict to complement sameSuffix by providing a map of any poser file suffix to
#					its opposite compression version to speed inexact search for files.
# v1.15	20191004	Incorporate Snarlygribbly's (Royston Harwood) fix for Poser 11.2 poser.AppVersion() format change 
#					which previously split the full version string into a.b.c .build, but is now simply a.b.build. 
#					The fix returns a.b.0.build
###############################################################################################

PoserUserInterfaceVersion = '1.15'
POSER_USERINTERFACE_VERSION = 'POSERUSERINTERFACE_VERSION'
debug = False

import os
import re
import poser
import PoserPrefs
#reload(PoserPrefs)
from collections import OrderedDict, namedtuple

millimetresPerPNU = 2621.280
AutoScales = [ 'Exact Size', 'Fit to Preview', 'Match to Preview' ]
ResolutionScales = [ 'Full', 'Half', 'Quarter' ]
VisibleHidden = [ 'Visible', 'Hidden' ]
CameraModels = { 0 : 'poser', 1 : 'real', 2 : 'depth', 3 : 'ortho', None : '' } # Ortho is a sub-type of Poser
CameraNames = ( 'MAIN_CAMERA', 'AUX_CAMERA', 'POSE_CAMERA', 'STD_CAMERA', 'SIDE_CAMERA', 'RIGHT_CAMERA', 'TOP_CAMERA', \
				'BOTTOM_CAMERA', 'FRONT_CAMERA', 'BACK_CAMERA', 'FACE_CAMERA', 'LHAND_CAMERA', 'RHAND_CAMERA' )
CameraParmCodes = [ poser.kParmCodeFOCAL, poser.kParmCodeXROT, poser.kParmCodeYROT, poser.kParmCodeZROT, \
					poser.kParmCodeXTRAN, poser.kParmCodeYTRAN, poser.kParmCodeZTRAN, poser.kParmCodeFOCUSDISTANCE ]
CameraPerspectiveParm = 'Perspective' # No typeCode so must find parameter by name.
CameraUnitScaleParm = 'UnitScaleFactor'
CameraHyperFocusParm = 'HyperFocus'
CameraCircleOfConfusionParm = 'CircleOfConfusion'
CameraFarFocusParm = 'FarFocus'
CameraDepthOfFieldParm = 'DepthOfField'
CameraUnitScaleName = 'Unit Scale Factor'
CameraHyperFocusName = 'HyperFocus'
CameraCircleOfConfusionName = 'Circle Of Confusion ({})'
CameraFarFocusName = 'Far Focus'
CameraDepthOfFieldName = 'Depth Of Field'
CircleOfConfusion = 0.03 # mm
UNIT_SCALE_FACTOR = 'UNIT_SCALE_FACTOR'
UNIT_SCALE_TYPE = 'UNIT_SCALE_TYPE'
UnitScaleFactor = 1.0 # PNU
UnitScaleType = 0 # PNU
UnitTypeName = [ 'Poser native units', 'Inches', 'Feet', 'Millimetres', 'Centimetres', 'Metres' ]
UnitTypeAbbreviation = [ 'PNU', '"', "'", 'mm', 'cm', 'm' ]
USE_COMPRESSION = 'USE_COMPRESSION'
UseCompression = 0
TestParmName = 'RemoveMe'
PPM_HASKEYATFRAME = 'HasKeyAtFrame'
PPM_ISCONTROLPROP = 'IsControlProp'
PoserPythonMethod = { PPM_HASKEYATFRAME : None, \
					  PPM_ISCONTROLPROP : None } # method availability test dict
NodeInputCodeName = {	poser.kNodeInputCodeNONE : 'None', # -1
						poser.kNodeInputCodeFLOAT : 'Float', # 0
						poser.kNodeInputCodeCOLOR : 'Color', # 1
						poser.kNodeInputCodeVECTOR : 'Vector', # 2
						poser.kNodeInputCodeSTRING : 'String', # 3
						poser.kNodeInputCodeBOOLEAN : 'Boolean', # 4
						poser.kNodeInputCodeINTEGER : 'Integer', # 5
						poser.kNodeInputCodeMENU : 'Menu' # 6
					}
ParmCodeName = {	poser.kParmCodeXROT : 'rotateX', \
					poser.kParmCodeYROT : 'rotateY', \
					poser.kParmCodeZROT : 'rotateZ', \
					poser.kParmCodeXTRAN : 'translateX', \
					poser.kParmCodeYTRAN : 'translateY', \
					poser.kParmCodeZTRAN : 'translateZ', \
					poser.kParmCodeXSCALE : 'scaleX', \
					poser.kParmCodeYSCALE : 'scaleY', \
					poser.kParmCodeZSCALE : 'scaleZ', \
					poser.kParmCodeASCALE : 'scale', \
					11 : 'aspect', \
					poser.kParmCodeFOCAL : 'focal', \
					13 : 'aperture', \
					poser.kParmCodeHITHER : 'hither', \
					poser.kParmCodeYON : 'yon', \
					17 : 'xOffsetA', \
					18 : 'xOffsetB', \
					19 : 'yOffsetA', \
					20 : 'yOffsetB', \
					21 : 'zOffsetA', \
					22 : 'zOffsetB', \
					poser.kParmCodeKDRED : 'kdRed', \
					poser.kParmCodeKDGREEN : 'kdGreen', \
					poser.kParmCodeKDBLUE : 'kdBlue', \
					poser.kParmCodeTAPERX : 'taperX', \
					poser.kParmCodeTAPERY : 'taperY', \
					poser.kParmCodeTAPERZ : 'taperZ', \
					poser.kParmCodeKDINTENSITY : 'kdIntensity', \
					30 : 'jointX', \
					31 : 'jointY', \
					32 : 'jointZ', \
					33 : 'twistX', \
					34 : 'twistY', \
					35 : 'twistZ', \
					36 : 'smoothScale', \
					37 : 'camAutoCenterX', \
					38 : 'camAutoCenterY', \
					39 : 'camAutoScale', \
					poser.kParmCodeDEPTHMAPSIZE : 'depthMapSize', \
					poser.kParmCodeDEPTHMAPSTRENGTH : 'depthMapStrength', \
					poser.kParmCodeTARGET : 'targetGeom', \
					poser.kParmCodeGEOMCHAN : 'geomChan', \
					poser.kParmCodeCENTER : 'kParmCodeCENTER', \
					poser.kParmCodeCURVE : 'curve', \
					poser.kParmCodeGRASP : 'handGrasp', \
					poser.kParmCodeTGRASP : 'thumbGrasp', \
					poser.kParmCodeSPREAD : 'handSpread', \
					poser.kParmCodeDEFORMERPROP : 'deformerPropChan', \
					poser.kParmCodeWAVEAMPLITUDE : 'waveAmplitude', \
					poser.kParmCodeWAVEFREQUENCY : 'waveFrequency', \
					poser.kParmCodeWAVELENGTH : 'waveLength', \
					poser.kParmCodeWAVESTRETCH : 'waveStretch', \
					poser.kParmCodeWAVESINUSOIDAL : 'waveSinusoidal', \
					poser.kParmCodeWAVESQUARE : 'waveRectangular', \
					poser.kParmCodeWAVETRIANGULAR : 'waveTriangular', \
					poser.kParmCodeWAVETURBULENCE : 'waveTurbulence', \
					58 : 'camAutoFocal', \
					poser.kParmCodeLITEFALLOFFSTART : 'liteFalloffStart', \
					poser.kParmCodeLITEFALLOFFEND : 'liteFalloffEnd', \
					poser.kParmCodeLITEATTENSTART : 'liteAttenStart', \
					poser.kParmCodeWAVEPHASE : 'wavePhase', \
					poser.kParmCodeWAVEAMPLITUDENOISE : 'waveAmplitudeNoise', \
					poser.kParmCodeWAVEOFFSET : 'waveOffset', \
					poser.kParmCodeVALUE : 'valueParm', \
					poser.kParmCodePOINTAT : 'pointAtParm', \
					poser.kParmCodeLITEATTENEND : 'liteAttenEnd', \
					poser.kParmCodeCLOTHDYNAMICS : 'clothDynamicsParm', \
					poser.kParmCodeHAIRDYNAMICS : 'hairDynamicsParm', \
					poser.kParmCodeDYNAMICPARENT : 'kParmCodeDYNAMICPARENT', \
					93 : 'perspective', \
					94 : 'forceAmplitude', \
					102 : 'shaderNodeParm', \
					103 : 'simpleFloat', \
					poser.kParmCodeFOCUSDISTANCE : 'focusDistance', \
					poser.kParmCodeFSTOP : 'fStop', \
					poser.kParmCodeSHUTTEROPEN : 'shutterOpen', \
					poser.kParmCodeSHUTTERCLOSE : 'shutterClose', \
					109 : 'visibility', \
					111 : 'constraintParm', \
					poser.kParmCodeSOFTDYNAMICS : 'kParmCodeSOFTDYNAMICS', \
					118 : 'orientationX', \
					119 : 'orientationY', \
					120 : 'orientationZ', \
					122 : 'apertureRatio', \
					123 : 'apertureBlades', \
					124 : 'apertureBladesRotation' \
				 }
# subType Names for simpleFloat parameter TypeCode 103 (Not yet exposed to python in v9.0.3.23027
# subType SubTypeName follows interpStyleLocked keyword in simpleFloat parameters
FloatSubTypeNames = { \
						0 : 'SpreadAngle', \
						1 : 'DistRange', \
						2 : 'TurbulenceStrength', \
					}
ValueOpTypeNames = { \
					poser.kValueOpTypeCodeDELTAADD : 'valueOpDeltaAdd', \
					poser.kValueOpTypeCodeDIVIDEBY : 'valueOpDivideBy', \
					poser.kValueOpTypeCodeDIVIDEINTO : 'valueOpDivideInto', \
					poser.kValueOpTypeCodeKEY : 'valueOpKey', \
					poser.kValueOpTypeCodeMINUS : 'valueOpMinus', \
					poser.kValueOpTypeCodePLUS : 'valueOpPlus', \
					poser.kValueOpTypeCodePYTHONCALLBACK : 'valueOpPythonCallBack', \
					poser.kValueOpTypeCodeTIMES : 'valueOpTimes' \
				 }
SimpleValueOpTypeCodes = { \
							poser.kValueOpTypeCodeDIVIDEBY : 'valueOpDivideBy', \
							poser.kValueOpTypeCodeDIVIDEINTO : 'valueOpDivideInto', \
							poser.kValueOpTypeCodeMINUS : 'valueOpMinus', \
							poser.kValueOpTypeCodePLUS : 'valueOpPlus', \
							poser.kValueOpTypeCodeTIMES : 'valueOpTimes' \
					   }
ScaleAxis = { 	poser.kParmCodeXSCALE : 'X', \
				poser.kParmCodeYSCALE : 'Y', \
				poser.kParmCodeZSCALE : 'Z' }
RotAxis = 	{	poser.kParmCodeXROT : 'X', \
				poser.kParmCodeYROT : 'Y', \
				poser.kParmCodeZROT : 'Z' }
TransAxis = {	poser.kParmCodeXTRAN : 'X', \
				poser.kParmCodeYTRAN : 'Y', \
				poser.kParmCodeZTRAN : 'Z' }
ScaleParmCodes = [ \
					poser.kParmCodeXSCALE, \
					poser.kParmCodeYSCALE, \
					poser.kParmCodeZSCALE, \
					poser.kParmCodeASCALE \
				 ]
AnimSetNameFmt = 'AnimSet {}' # Default name format for animSets until their names are exposed post 11.0.5.33735
AnimSetNameAttr = 'Name'
AnimSetExtensionAttr = 'Extension'
CustomDataKeyDelimiter = ';'
CustomDataListKey = 'Keys'
CustomDataFrameDelimiter = '#'
CustomDataPoseNameKey = 'PoseName' # customData value for this key may contain path information as well
CustomDataPoseNameFrameFmt = '{}{}{:g}' # Use CustomDataPoseNameKey, CustomDataFrameDelimiter and frame number
Custom = namedtuple( 'Custom', [ 'storeWithPoses', 'storeWithMaterials', 'value' ] ) # customData attributes
compressedSuffixes = ( '.cmz', '.fcz', '.crz', '.hrz', '.hdz', '.ltz', '.p2z', '.ppz', '.pzz' ) # Alpha order of method name
uncompressedSuffixes = ( '.cm2', '.fc2', '.cr2', '.hr2', '.hd2', '.lt2', '.pz2', '.pp2', '.pz3' ) # Alpha order of method name
sameSuffix = { 	'.cm2': '.cm2', '.cmz': '.cm2', \
				'.cr2': '.cr2', '.crz': '.cr2', \
				'.fc2': '.fc2', '.fcz': '.fc2', \
				'.hd2': '.hd2', '.hdz': '.hd2', \
				'.hr2': '.hr2', '.hrz': '.hr2', \
				'.lt2': '.lt2', '.ltz': '.lt2', \
				'.mc6': '.mc6', '.mcz': '.mc6', \
				'.mt5': '.mt5', '.mz5': '.mt5', \
				'.obj': '.obj', '.obz': '.obj', \
				'.pz2': '.pz2', '.p2z': '.pz2', \
				'.pz3': '.pz3', '.pzz': '.pz3' } # Map any poser file suffix to its uncompressed equivalent
otherSuffix = { '.cm2': '.cmz', '.cmz': '.cm2', \
				'.cr2': '.crz', '.crz': '.cr2', \
				'.fc2': '.fcz', '.fcz': '.fc2', \
				'.hd2': '.hdz', '.hdz': '.hd2', \
				'.hr2': '.hrz', '.hrz': '.hr2', \
				'.lt2': '.ltz', '.ltz': '.lt2', \
				'.mc6': '.mcz', '.mcz': '.mc6', \
				'.mt5': '.mz5', '.mz5': '.mt5', \
				'.obj': '.obz', '.obz': '.obj', \
				'.pz2': '.p2z', '.p2z': '.pz2', \
				'.pz3': '.pzz', '.pzz': '.pz3' } # Map any poser file suffix to its opposite compression equivalent
CameraSuffix = 0
FaceSuffix = 1
FigureSuffix = 2
HairSuffix = 3
HandSuffix = 4
LightSuffix = 5
PoseSuffix = 6
PropSuffix = 7
SceneSuffix = 8
SaveMethod = {	uncompressedSuffixes[ CameraSuffix	 ] : poser.Scene().SaveLibraryCamera, \
				uncompressedSuffixes[ FaceSuffix	 ] : poser.Scene().SaveLibraryFace, \
				uncompressedSuffixes[ FigureSuffix	 ] : poser.Scene().SaveLibraryFigure, \
				uncompressedSuffixes[ HairSuffix	 ] : poser.Scene().SaveLibraryHair, \
				uncompressedSuffixes[ HandSuffix	 ] : poser.Scene().SaveLibraryHand, \
				uncompressedSuffixes[ LightSuffix	 ] : poser.Scene().SaveLibraryLight, \
				uncompressedSuffixes[ PoseSuffix	 ] : poser.Scene().SaveLibraryPose, \
				uncompressedSuffixes[ PropSuffix	 ] : poser.Scene().SaveLibraryProp, \
				uncompressedSuffixes[ SceneSuffix	 ] : poser.SaveDocument }

def TestMethods( theParm=None ):
	"""
	This method determines whether Poser Python supports the HasKeyAtFrame parameter method.
	This method determines whether Poser Python supports the IsControlProp actor method.
	
	theParm:	An optionally supplied parameter to use for the method existence test
	"""
	global PoserPythonMethods
	global TestParmName
	global PPM_HASKEYATFRAME
	global PPM_ISCONTROLPROP
	
	RemoveTestParm = False
	if theParm is None:
		scene = poser.Scene()
		actor = scene.Actors()[ 0 ] # Scene should always have at least UNIVERSE actor
		parm = None
		try: # Previously assumed UNIVERSE actor always had parameters
			parm = actor.Parameters()[ 0 ] # assume UNIVERSE actor always has parameters
		except: # Let's create a parameter to test on
			if parm is None: 
				parm = actor.CreateValueParameter( TestParmName )
				RemoveTestParm = True
			else: # We had some other problem, so Crash and burn - major problems with the environment
				raise Exception, 'Actor "{}" has no parameters!'.format( actor.InternalName() )
	else:
		parm = theParm
		actor = theParm.Actor() # We need an actor for the IsControlProp method test
	if PoserPythonMethod[ PPM_ISCONTROLPROP ] is None: # Not tested yet
		try:
			test = None
			test = actor.IsControlProp()
			if test is not None:
				PoserPythonMethod[ PPM_ISCONTROLPROP ] = True
		except:
			PoserPythonMethod[ PPM_ISCONTROLPROP ] = False
	if PoserPythonMethod[ PPM_HASKEYATFRAME ] is None: # Not tested yet
		try:
			test = None
			test = parm.HasKeyAtFrame( 0 )
			if test is not None:
				PoserPythonMethod[ PPM_HASKEYATFRAME ] = True
		except:
			PoserPythonMethod[ PPM_HASKEYATFRAME ] = False
	if RemoveTestParm: # actor and parm to be removed must exist if we got here
		actor.RemoveValueParameter( TestParmName )

def ActorTypeName( theActor ):
	"""
	Return the actor type string which precedes the actor name in poser files.
	NOTE: Fallback detection methods for controlProp and groupingObject prop actors are used for environments where
	NOTE: specific identification methods have not been exposed to poser python as per version 11.0.6.33735
	
	theActor	: the actor whose type string is to be returned.
	"""
	if theActor.IsBodyPart(): # actor or refactor
		return 'actor'
	elif theActor.IsCamera():
		return 'camera'
	elif theActor.IsLight():
		return 'light'
	elif theActor.IsProp():
		if theActor.IsBase():
			return 'baseProp'
		elif theActor.IsDeformer():
			return 'magnetDeformerProp'
		elif theActor.IsHairProp():
			return 'hairProp'
		elif theActor.IsZone():
			return 'sphereZoneProp'
		else: # prop or controlProp or groupingObject
			try:
				if theActor.IsControlProp(): # New method for Poser 11
					return 'controlProp'
				else:
					try: # Catch os.path method exceptions if theActor.GeomFileName() is None
						if os.path.splitext( os.path.basename( theActor.GeomFileName() ) )[ 0 ] == 'grouping':
							return 'groupingObject' # Not yet exposed by python method in Poser 11.0.6.33735
					except:
						return 'prop'
					else:
						return 'prop'
			except:
				namePart = theActor.InternalName().split(':')
				if namePart[0] in [ 'FocusDistanceControl', 'CenterOfMass', 'GoalCenterOfMass' ]:
					return 'controlProp'
				else:
					try: # Catch os.path method exceptions if theActor.GeomFileName() is None
						if os.path.splitext( os.path.basename( theActor.GeomFileName() ) )[ 0 ] == 'grouping':
							return 'groupingObject' # Not yet exposed by python method in Poser 11.0.6.33735
					except:
						return 'prop'
					else:
						return 'prop'
	else: # Return a usable default
		return 'actor'

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
	global PoserPythonMethod
	
	theParm = theCamera.ParameterByCode(theParmCode)
	if theParm is None:
		if inherit and GetCameraModel( theCamera ) == 2: # Depth camera, so try inherited parameter
			theParm = theCamera.Parent().ParameterByCode( theParmCode )
		if theParm is None:
			print 'Selected Camera', theCamera.Name(), 'cannot be aimed.'
			raise Exception,  'CameraError: {} missing required parameter'.format( theCamera.Name() )
	else: # Test availability of poser python methods
		TestMethods( theParm )
	return theParm

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
	if not theCamera.IsCamera():
		return None # Not a camera actor
	theParm = theCamera.ParameterByCode(poser.kParmCodeXROT)
	if theParm is None: # The shadow cameras are parented to lights and have no rotation parms
		return 2 # depth
	theParm = theCamera.ParameterByCode(poser.kParmCodeFOCAL)
	if theParm.Value() == 0.0: # Can fool this if any camera has focal length changed to 0, so
		theParm = theCamera.ParameterByCode(poser.kParmCodeZTRAN)
		if theParm.Hidden(): # This is a poser, ortho camera (only x,y translations visible)
			return 3 # ortho. Actually a sub-type of poser cameraModel
	theParm = theCamera.Parameter(CameraPerspectiveParm)
	if theParm.Hidden(): # This is a real cameraModel camera, e.g. Dolly Camera
		return 1
	return 0 # poser cameraModel (orbiting)

def UserCreated( theCamera ):
	"""
	Return whether theCamera is userCreated, based on whether its InternalName() is not in the set of Poser standard
	camera names listed in the global CameraNames.
	NOTE: Returns int(1) if userCreated or int(0) if a standard poser or depth camera or not a camera actor.
	
	theCamera	: the camera actor whose userCreated status is to be returned.
	"""
	global CameraNames
	
	if theCamera.IsCamera(): # Exclude non-camera actors
		if GetCameraModel( theCamera ) != 2: # Exclude depth cameras
			userCreated = theCamera.InternalName() not in CameraNames
		else:
			userCreated = False
	else:
		userCreated = False
	return int( userCreated )

def PNUToUnits(PNU):
	"""
	This method returns the current Poser UI units equivalent of PNU in Poser Native Units.
	
	PNU						: A length in Poser Native Units (1 PNU = 100 inches = 8.6 feet = 2.62128 metres)
	global UnitScaleFactor	: The current Poser UI unit selection read from the PoserPrefs file
	"""
	global UnitScaleFactor
	
	return PNU * UnitScaleFactor

def UnitsToPNU(units):
	"""
	This method returns the Poser Native Units equivalent of units in current Poser UI units.
	
	units					: A length in current Poser User Interface units.
	global UnitScaleFactor	: The current Poser UI unit selection read from the PoserPrefs file
	"""
	global UnitScaleFactor
	
	return units / UnitScaleFactor

def MillimetresToPNU(mm):
	"""
	This method returns the Poser Native Units equivalent of mm (in millimetres).
	
	mm							: A length in millimetres.
	global millimetresPerPNU	: The ratio 2621.28 millimetres per Poser Native Unit
	"""
	global millimetresPerPNU
	
	return mm / millimetresPerPNU

def PNUToMillimetres(PNU):
	"""
	This method returns the millimetre equivalent of PNU (in Poser Native Units).
	
	PNU							: A length in Poser Native Units
	global millimetresPerPNU	: The ratio 2621.28 millimetres per Poser Native Unit
	"""
	global millimetresPerPNU
	
	return PNU * millimetresPerPNU

def HyperFocal(f, N, c):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# returned units are millimetres
	"""
	return f + ( ( f * f ) / ( N * c ) )

def FStop(f, s, c):
	"""
	# f = focal length in millimetres
	# s = focus distance in millimetres
	# c = circle of confusion in millimetres
	# returned value is a scalar (unitless) representing the maximum DOF when focus distance = hyperfocus
	"""
	return ( f * f ) / ( ( s - f ) * c )

def NearFocus(f, N, c, s):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# s = focus distance in millimetres
	# returned units are millimetres
	"""
	H = HyperFocal(f, N, c)
	return s * ( H - f ) / ( H + s - ( 2 * f ) )

def FarFocus(f, N, c, s):
	"""
	# f = focal length in millimetres
	# N = fStop
	# c = circle of confusion in millimetres
	# s = focus distance in millimetres
	# returned units are millimetres
	"""
	H = HyperFocal(f, N, c)
	return s * ( H - f ) / ( H - s )

def GetAnimSetNames():
	"""
	Return a list of names of animSets in the poser scene. AnimSet Names are not yet exposed to Python in 11.0.6.33735
	Names will either consist of the value of the 'Name' attribute of the animSet or the animSets() list index in the
	form 'AnimSet {}'.format(index)
	"""
	global AnimSetNameFmt
	global AnimSetNameAttr
	
	AnimSetNameList = []
	setNum = 0
	for animSet in poser.Scene().AnimSets():
		foundName = False
		for attrib in animSet.Attributes():
			if attrib[0] == AnimSetNameAttr:
				foundName = True
				setName = attrib[1]
				break
		setNum += 1
		if not foundName: # AnimSet names are not currently exposed to python in Poser Pro 11.0.6.33735
			setName = AnimSetNameFmt.format( setNum )
		AnimSetNameList.append(setName)
	return AnimSetNameList

def GetAnimSetAttribute( theAnimSetName, theAttribute ):
	"""
	Given an existing AnimSet name, return the value of the attribute with key theAttribute or None if not found.
	
	theAnimSetName	The name of the animSet whose attribute value is to be returned.
	theAttribute	The name of the attribute whose value is to be returned.
	"""
	attribute = None # Indicate no such attribute in animSet
	try:
		animSet = poser.Scene().AnimSet( theAnimSetName )
		for attrib in animSet.Attributes(): # attrib is a (key, value) tuple
			if attrib[ 0 ] == theAttribute:
				attribute = attrib[ 1 ]
				break
	except: # Indicate no such attribute in animSet
		pass
	return attribute

def GetAnimSetActorParms( theAnimSetName ):
	"""
	Given an existing AnimSet name, return an OrderedDict of actors and their parameters specified by the AnimSet.
	Return None if no such named animSet found
	NOTE: Though the animSet will naturally return a list of parameters, their actors must be subsequently determined.
	NOTE: We are making the assumption that all of the actors are either unparented props or belong to a single figure.
	NOTE: Should multiple figures be referenced by the animSet.Parameters() list, the dict returned should probably
	NOTE: be indexed by figure and actor, rather than just actor, so saving schemes can wrap the parameters.
	"""
	try:
		animSet = poser.Scene().AnimSet( theAnimSetName )
		animSetActors = OrderedDict()
		for parm in animSet.Parameters():
			actor = parm.Actor()
			if actor in animSetActors:
				animSetActors[ actor ].append( parm )
			else:
				animSetActors[ actor ] = [ parm ]
	except:
		animSetActors = None # Indicate no such animSet in scene
	return animSetActors

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
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global CustomDataFrameDelimiter
	global CustomDataPoseNameKey
	global CustomDataPoseNameFrameFmt
	
	poseName = None
	keyFound = None
	if theFrame is None:
		theFrame = poser.Scene().Frame()
	framekey = CustomDataPoseNameFrameFmt.format( CustomDataPoseNameKey, CustomDataFrameDelimiter, theFrame )
	if useActor: # Try theActor PoseName before testing theFigure
		theObject = theActor
	elif theFigure is not None: # Figure PoseName will override individual actor PoseName
		theObject = theFigure
	else: # Check theActor PoseName
		theObject = theActor
	if theObject is None:
		theObject = poser.Scene().CurrentActor()
	customKeys = theObject.CustomData( CustomDataListKey )
	keys = []
	if customKeys is not None: # Extract existing customData Keys value into keys list
		keys = customKeys.split( CustomDataKeyDelimiter )
		if framekey in keys:
			poseName = theObject.CustomData( framekey )
			keyFound = framekey
		elif useLast and CustomDataPoseNameKey in keys:
			poseName = theObject.CustomData( CustomDataPoseNameKey )
			keyFound = CustomDataPoseNameKey
	if poseName is not None:
		if baseOnly:
			poseName = os.path.basename( poseName )
		if stripExt:
			poseName, ext = os.path.splitext( poseName )
	elif useActor: # No actor PoseName customData, so try falling back to theFigure
		poseName, keyFound = GetCustomDataPoseName( theFigure, theActor, theFrame, useLast, baseOnly, stripExt, False )
	return poseName, keyFound

def StringSplitByNumbers(x):
	"""
	Regular expression sort key for numeric order sorting of digit sequences in alphanumeric strings
	Credit: Matt Connolly (http://code.activestate.com/recipes/users/4177092/)
	"""
	r = re.compile('(\d+)')
	l = r.split(x)
	return [int(y) if y.isdigit() else y for y in l]

def ListAllCustomData( theObject=None ):
	"""
	Print a list of all customData for theObject, or the entire scene, with frame references numerically sorted
	Excludes the CustomDataListKey itself, which is only there to provide missing customData lookup functionality
	
	theObject:	figure or actor type scene object. If None, report customData for the entire scene
	"""
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global CustomDataFrameDelimiter
	global CustomDataPoseNameKey
	global CustomDataPoseNameFrameFmt
	
	if theObject is not None:
		customKeys = theObject.CustomData( CustomDataListKey )
		if customKeys is not None:
			keyList = sorted( customKeys.split( CustomDataKeyDelimiter ), key = StringSplitByNumbers )
			keyList = [ elem for elem in keyList if elem != CustomDataListKey ]
			for key in keyList:
				data = theObject.CustomData( key )
				print '{}, {} "{}"'.format( theObject.Name(), key, data )
	else:
		scene = poser.Scene()
		for actor in scene.Actors(): # This parses all unparented actors in the scene as well as actors in figures.
			customKeys = actor.CustomData( CustomDataListKey )
			if customKeys is not None:
				keyList = sorted( customKeys.split( CustomDataKeyDelimiter ), key = StringSplitByNumbers )
				keyList = [ elem for elem in keyList if elem != CustomDataListKey ]
				for key in keyList:
					data = actor.CustomData( key )
					print '{}, {} "{}"'.format( actor.Name(), key, data )
		else:
			for figure in scene.Figures():
				customKeys = figure.CustomData( CustomDataListKey )
				if customKeys is not None:
					keyList = sorted( customKeys.split( CustomDataKeyDelimiter ), key = StringSplitByNumbers )
					keyList = [ elem for elem in keyList if elem != CustomDataListKey ]
					for key in keyList:
						data = figure.CustomData( key )
						print '{}, {} "{}"'.format( figure.Name(), key, data )

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
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global CustomDataFrameDelimiter
	global CustomDataPoseNameKey
	global CustomDataPoseNameFrameFmt
	
	if len( theData ) > 0: # Need to maintain customData Keys list
		customKeys = theObject.CustomData( CustomDataListKey )
		keys = []
		if customKeys is not None: # Extract existing customData Keys value into keys list
			keys = customKeys.split( CustomDataKeyDelimiter )
		for (key, data) in theData.iteritems():
			if key not in keys: # Avoid duplicating existing keys
				keys.append( key )
			theObject.SetCustomData( key, data.value, data.storeWithPoses, data.storeWithMaterials )
			if key == CustomDataPoseNameKey: # Replicate this customData for the current frame
				framekey = CustomDataPoseNameFrameFmt.format( CustomDataPoseNameKey, CustomDataFrameDelimiter, \
																								poser.Scene().Frame() )
				if framekey not in keys:
					keys.append( framekey )
				theObject.SetCustomData( framekey, data.value, data.storeWithPoses, data.storeWithMaterials )
		customKeys = CustomDataKeyDelimiter.join( keys )
		theObject.SetCustomData( CustomDataListKey, customKeys, 0, 0 ) # Save lookup for customData Keys


# Override Poser 11.2 AppVersion() method format change
if len( poser.AppVersion().split( '.' ) ) < 4:
	oldav = poser.AppVersion
	newav = poser.AppVersion()

	def AppV():
		global newav
	
		v = newav.split( '.' )
		v[ 1 ] = v[ 1 ].strip()
		v[ 2 ] = str( int( v[ 2 ] ) + 40000 )
		return '{}.{}.0.{}'.format( v[ 0 ], v[ 1 ], v[ 2 ] )

	poser.AppVersion = AppV

# Investigate the current poser environment
TestMethods()

# Instantiate preferences. Defaults to Poser's own preferences.
prefs = PoserPrefs.Preferences()

# Initialise preferences OrderedDict with what we're looking for.
prefs.preferences[ UNIT_SCALE_FACTOR ] = 1.0 # PNU
prefs.preferences[ UNIT_SCALE_TYPE ] = 0 # PNU
prefs.preferences[ USE_COMPRESSION ] = 0 # False

# Load specified preferences
prefs.Load()
UnitScaleFactor = float( prefs.preferences[ UNIT_SCALE_FACTOR ] )
UnitScaleType = int( prefs.preferences[ UNIT_SCALE_TYPE ] )
UseCompression = int( prefs.preferences[ USE_COMPRESSION ] )
if debug:
	for pref in prefs.preferences.keys():
		print '   {} : {}'.format( pref, prefs.preferences[ pref ] )
	print 'UnitScaleFactor = {}'.format( UnitScaleFactor )
	print 'UnitScaleType = {}'.format( UnitTypeName[ UnitScaleType ] )
	print 'UseCompression = {}'.format( UseCompression )

### END ###