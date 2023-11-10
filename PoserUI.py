# PoserUI.py
# (c) 2014-2023 GeoffIX (Geoff Hicks)
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
# v1.16	20191025	Added GetCustomDataKeys(), SetCustomDataKeys() and AddCustomData() methods to simplify management 
#					of CustomData by recording the keys used.
# v1.17	20191206	Added symmetric LoadMethod dispatcher dict for loading library files based on file extension.
# v1.18	20201019	Update AppVersion() method override to account for Poser 12, giving build numbers > 41000.
# v2.0	20201107	Replace print statement with function call for Python3 compatibility in Poser12.
#					Python3 raise only takes a single Exception instance or class with explicit parameters.
#					Explicitly import PoserPrefs from PoserLib.
# v2.1	20210620	Replace Python2 only OrderedDict iteritems() method with iter(dict.items()) for Python3. 
# v2.2	20220401	Add support for double-quote delimited CustomData Key values used by Poser 12.
#					Add awareness of AllCustomData() method in Poser 12.
#		20220402	Use animSet.Name() method if available.
#					New methods: GetFrameKey, GetLocationFrameKey, GetFrameCustomData, GetCustomDataLocation, 
#					ListCustomData.
#					Modified methods: GetPoseNameFrameKey, GetCustomDataPoseName, GetCustomDataKeys, SetCustomDataKeys,
#					AddCustomData, ListAllCustomData.
#					Use json.dumps() to serialise any dict or complex CustomData being printed.
#		20220530	New methods: GetMultiPoseFrameKey, GetCustomDataMultiPose.
# v2.3	20230814	Add dict ActorTypeNames with keys returned by the Poser GetIdType() method and string values.
#					Test for the GetIdType() actor method.
#					Add support for actor types measurementLine, measurementAngle, measurementCircle & 
#					measurementPolyLine.
#		20230818	Add support for scene object types controlHandleProp, curveProp, waveDeformerProp & coneForceFieldProp.
#		20230819	Add support for scene object type uniformForceFieldProp.
# v2.4	20231107	Add __version__ global for requirements comparisons.
# v2.5	20231110	Add support for 'Expression' CustomData.
########################################################################################################################
from __future__ import print_function

__version__ = '2.5.0'
PoserUserInterfaceVersion = __version__
POSER_USERINTERFACE_VERSION = 'POSERUSERINTERFACE_VERSION'
debug = False

import os
import re
import json
import poser
from PoserLib import PoserPrefs
#from importlib import reload
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
PPM_ALLCUSTOMDATA = 'AllCustomData'
PPM_ANIMSETNAME = 'AnimSetName'
PPM_GETIDTYPE = 'GetIdType'
ActorTypeNames = {  7 : 'actor',
					8 : 'camera',
					9 : 'light',
					12 : 'prop', # IsPropInstance
					15 : 'curveProp',
					16 : 'baseProp',
					18 : 'magnetDeformerProp',
					19 : 'waveDeformerProp',
					21 : 'sphereZoneProp',
					23 : 'hairProp',
					24 : 'uniformForceFieldProp',
					25 : 'coneForceFieldProp',
					26 : 'controlProp',
					28 : 'controlHandleProp',
					29 : 'groupingObject',
					34 : 'measurementLine',
					35 : 'measurementAngle',
					36 : 'measurementCircle',
					37 : 'measurementPolyline',
					}
PoserPythonMethod = { PPM_HASKEYATFRAME : None, \
					  PPM_ISCONTROLPROP : None, \
					  PPM_ALLCUSTOMDATA : None, \
					  PPM_ANIMSETNAME : None, \
					  PPM_GETIDTYPE : None } # method availability test dict
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
CustomDataFrameFmt = '{}{}{:g}' # Use CustomDataPoseNameKey, CustomDataFrameDelimiter and frame number
CustomDataLocationKey = 'Location' # customData value for this key may contain path & location information as well
CustomDataMultiPoseKey = 'MultiPose' # customData value for this key may contain path information as well
CustomDataPoseNameKey = 'PoseName' # customData value for this key may contain path information as well
CustomDataPoseNameFrameFmt = '{}{}{:g}' # Use CustomDataPoseNameKey, CustomDataFrameDelimiter and frame number
CustomDataExpressionKey = 'Expression' # customData value for this key may contain path information as well
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
LoadMethod = {	uncompressedSuffixes[ CameraSuffix	 ] : poser.Scene().LoadLibraryCamera, \
				uncompressedSuffixes[ FaceSuffix	 ] : poser.Scene().LoadLibraryFace, \
				uncompressedSuffixes[ FigureSuffix	 ] : poser.Scene().LoadLibraryFigure, \
				uncompressedSuffixes[ HairSuffix	 ] : poser.Scene().LoadLibraryHair, \
				uncompressedSuffixes[ HandSuffix	 ] : poser.Scene().LoadLibraryHand, \
				uncompressedSuffixes[ LightSuffix	 ] : poser.Scene().LoadLibraryLight, \
				uncompressedSuffixes[ PoseSuffix	 ] : poser.Scene().LoadLibraryPose, \
				uncompressedSuffixes[ PropSuffix	 ] : poser.Scene().LoadLibraryProp, \
				uncompressedSuffixes[ SceneSuffix	 ] : poser.OpenDocument }
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
	This method determines whether Poser Python supports the AllCustomData actor method.
	This method determines whether Poser Python supports the Name animSet method.
	This method determines whether Poser Python supports the GetTypId actor method.
	
	theParm:	An optionally supplied parameter to use for the method existence test
	"""
	global PoserPythonMethod
	global TestParmName
	global PPM_HASKEYATFRAME
	global PPM_ISCONTROLPROP
	global PPM_ALLCUSTOMDATA
	global PPM_ANIMSETNAME
	global PPM_GETIDTYPE
	
	RemoveTestParm = False
	RemoveAnimSet = False
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
				raise Exception( 'Actor "{}" has no parameters!'.format( actor.InternalName() ) )
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
	if PoserPythonMethod[ PPM_ALLCUSTOMDATA ] is None: # Not tested yet
		try:
			test = actor.AllCustomData() # This may validly return None without exception
			PoserPythonMethod[ PPM_ALLCUSTOMDATA ] = True
		except:
			PoserPythonMethod[ PPM_ALLCUSTOMDATA ] = False
	if PoserPythonMethod[ PPM_ANIMSETNAME ] is None: # Not tested yet
		scene = poser.Scene()
		try:
			aset = scene.CreateAnimSet( TestParmName )
			RemoveAnimSet = True
		except poser.error: # Animset already existed, so don't remove
			aset = scene.AnimSet( TestParmName )
		try:
			test = aset.Name()
			PoserPythonMethod[ PPM_ANIMSETNAME ] = True
		except:
			PoserPythonMethod[ PPM_ANIMSETNAME ] = False
	if PoserPythonMethod[ PPM_GETIDTYPE ] is None: # Not tested yet
		try:
			test = None
			test = actor.GetIdType()
			if test is not None:
				PoserPythonMethod[ PPM_GETIDTYPE ] = True
		except:
			PoserPythonMethod[ PPM_GETIDTYPE ] = False
	if RemoveTestParm: # actor and parm to be removed must exist if we got here
		actor.RemoveValueParameter( TestParmName )
	if RemoveAnimSet:
		scene.DeleteAnimSet( TestParmName )

def ActorTypeName( theActor ):
	"""
	Return the actor type string which precedes the actor name in poser files.
	NOTE: Fallback detection methods for controlProp and groupingObject prop actors are used for environments where
	NOTE: specific identification methods have not been exposed to poser python as per version 11.0.6.33735
	NOTE: The four measurement prop types are indistinguishable using legacy methods, 
	NOTE: so they are ignored if GetIdType() is unavailable.
	
	theActor	: the actor whose type string is to be returned.
	"""
	global ActorTypeNames
	
	try:
		return ActorTypeNames[ theActor.GetIdType() ]
	except: # Use the old method
		if theActor.IsBodyPart(): # actor or refactor
			return 'actor'
		elif theActor.IsCamera():
			return 'camera'
		elif theActor.IsLight():
			return 'light'
		elif theActor.IsProp(): # Includes measurements but indistinguishable
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
			print( 'Selected Camera', theCamera.Name(), 'cannot be aimed.' )
			raise Exception(  'CameraError: {} missing required parameter'.format( theCamera.Name() ) )
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
	AnimSet names are now exposed in Poser 12.0.735, so that method is used if available.
	"""
	global PoserPythonMethod
	global PPM_ANIMSETNAME
	global AnimSetNameFmt
	global AnimSetNameAttr
	
	AnimSetNameList = []
	setNum = 0
	for animSet in ( poser.Scene().AnimSets() or [] ):
		if PoserPythonMethod[ PPM_ANIMSETNAME ]:
			setName = animSet.Name()
			foundName = True
		else:
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

def GetFrameKey( keyName=None, theFrame=None ):
	"""
	Return the customData 'keyName#nn' key matching the specified frame.
	If no frame is specified, use the current scene frame.
	If no keyName is specified, nothing will precede the frame delimiter.
	
	theFrame	The integer frame component of the 'keyName#nn' customData key to be returned. If None, default to
				the current scene frame
	"""
	global CustomDataFrameDelimiter
	global CustomDataFrameFmt
	
	if keyName is None:
		keyName = ''
	if theFrame is None:
		theFrame = poser.Scene().Frame()
	return CustomDataFrameFmt.format( keyName, CustomDataFrameDelimiter, theFrame )

def GetExpressionFrameKey( theFrame=None ):
	"""
	Return the customData 'Expression#nn' key matching the specified frame.
	If no frame is specified, use the current scene frame.
	
	theFrame	The integer frame component of the 'Expression#nn' customData key to be returned. If None, default to
				the current scene frame
	"""
	global CustomDataExpressionKey
	
	return GetFrameKey( CustomDataExpressionKey, theFrame )

def GetLocationFrameKey( theFrame=None ):
	"""
	Return the customData 'Location#nn' key matching the specified frame.
	If no frame is specified, use the current scene frame.
	
	theFrame	The integer frame component of the 'Location#nn' customData key to be returned. If None, default to
				the current scene frame
	"""
	global CustomDataLocationKey
	
	return GetFrameKey( CustomDataLocationKey, theFrame )

def GetMultiPoseFrameKey( theFrame=None ):
	"""
	Return the customData 'MultiPose#nn' key matching the specified frame.
	If no frame is specified, use the current scene frame.
	
	theFrame	The integer frame component of the 'MultiPose#nn' customData key to be returned. If None, default to
				the current scene frame
	"""
	global CustomDataMultiPoseKey
	
	return GetFrameKey( CustomDataMultiPoseKey, theFrame )

def GetPoseNameFrameKey( theFrame=None ): # Retained for legacy compatibility
	"""
	Return the customData 'PoseName#nn' key matching the specified frame.
	If no frame is specified, use the current scene frame.
	
	theFrame	The integer frame component of the 'PoseName#nn' customData key to be returned. If None, default to
				the current scene frame
	"""
	global CustomDataPoseNameKey
	
	return GetFrameKey( CustomDataPoseNameKey, theFrame )

def GetFrameCustomData( theFigure=None, theActor=None, keyName=None, theFrame=None, useLast=False, baseOnly=False, \
																			stripExt=False, useActor=False ):
	"""
	Check theFigure or theActor for customData 'keyName#nn' keys matching the specified keyName and frame.
	If both theFigure and theActor are None, default to the currently selected scene actor.
	If useLast is set, return the customData 'keyName' if 'keyName#nn' is absent for that frame.
	Return the customData value (or None if not found) and which key was located.
	
	theFigure	The figure, if any selected for saving
	theActor	In the absence of a selected figure, the actor whose customData 'keyName' is to be returned
	theFrame	The frame component of the 'keyName#nn' customData key being searched for. If None, default to 
				the current scene frame
	useLast		Allows the 'keyName' customData to be returned if frame specific version is absent
	baseOnly	Remove the path component and return only the basename
	stripExt	Remove the '.pz2' or other extension if True
	useActor	If theFigure is not None, try theActor before falling back to theFigure. (Single recursion)	
	"""
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global PoserPythonMethod
	global PPM_ALLCUSTOMDATA
	
	customData = None
	keyFound = None
	framekey = GetFrameKey( keyName, theFrame )
	if useActor: # Try theActor customData before testing theFigure
		theObject = theActor
	elif theFigure is not None: # Figure customData will override individual actor PoseName
		theObject = theFigure
	else: # Check theActor customData
		theObject = theActor
	if theObject is None:
		theObject = poser.Scene().CurrentActor()
	if PoserPythonMethod[ PPM_ALLCUSTOMDATA ]: # Manual CustomData key recording not required
		keys = list( ( theObject.AllCustomData() or {} ).keys() )
	else:
		customKeys = theObject.CustomData( CustomDataListKey )
		keys = []
		if customKeys is not None: # Extract existing customData Keys value into keys list
			keys = customKeys.split( CustomDataKeyDelimiter )
	if framekey in keys:
		customData = theObject.CustomData( framekey )
		keyFound = framekey
	elif useLast and keyName in keys:
		customData = theObject.CustomData( CustomDataPoseNameKey )
		keyFound = keyName
	if customData is not None and type( customData ) == str:
		if baseOnly:
			customData = os.path.basename( customData )
		if stripExt:
			customData, ext = os.path.splitext( customData )
	elif useActor: # No actor PoseName customData, so try falling back to theFigure
		customData, keyFound = GetFrameCustomData( theFigure, theActor, keyName, theFrame, useLast, baseOnly, stripExt, False )
	return customData, keyFound

def GetCustomDataExpression( theFigure=None, theActor=None, theFrame=None, useLast=False, baseOnly=False, \
																			stripExt=False, useActor=False ):
	"""
	Check theFigure or theActor for customData 'Expression#nn' keys matching the specified frame.
	If both theFigure and theActor are None, default to the currently selected scene actor.
	If useLast is set, return the customData 'Expression' if 'Expression#nn' is absent for that frame.
	Return the customData value (or None if not found) and which key was located.
	
	theFigure	The figure, if any selected for saving
	theActor	In the absence of a selected figure, the actor whose customData 'PoseName' is to be returned
	theFrame	The frame component of the 'Expression#nn' customData key being searched for. If None, default to 
				the current scene frame
	useLast		Allows the 'Expression' customData to be returned if frame specific version is absent
	baseOnly	Remove the path component and return only the basename (Ignored)
	stripExt	Remove the '.pz2' or other extension if True (Ignored)
	useActor	If theFigure is not None, try theActor before falling back to theFigure. (Single recursion)	
	"""
	global CustomDataExpressionKey
	
	# NOTE: Expression value is not a string, so baseOnly and stripExt parameters are ignored
	return GetFrameCustomData( theFigure, theActor, CustomDataExpressionKey, theFrame, useLast, False, False, useActor )

def GetCustomDataLocation( theFigure=None, theActor=None, theFrame=None, useLast=False, baseOnly=False, \
																			stripExt=False, useActor=False ):
	"""
	Check theFigure or theActor for customData 'Location#nn' keys matching the specified frame.
	If both theFigure and theActor are None, default to the currently selected scene actor.
	If useLast is set, return the customData 'Location' if 'Location#nn' is absent for that frame.
	Return the customData value (or None if not found) and which key was located.
	
	theFigure	The figure, if any selected for saving
	theActor	In the absence of a selected figure, the actor whose customData 'PoseName' is to be returned
	theFrame	The frame component of the 'Location#nn' customData key being searched for. If None, default to 
				the current scene frame
	useLast		Allows the 'Location' customData to be returned if frame specific version is absent
	baseOnly	Remove the path component and return only the basename (Ignored)
	stripExt	Remove the '.pz2' or other extension if True (Ignored)
	useActor	If theFigure is not None, try theActor before falling back to theFigure. (Single recursion)	
	"""
	global CustomDataLocationKey
	
	# NOTE: Location value is not a string, so baseOnly and stripExt parameters are ignored
	return GetFrameCustomData( theFigure, theActor, CustomDataLocationKey, theFrame, useLast, False, False, useActor )

def GetCustomDataMultiPose( theFigure=None, theActor=None, theFrame=None, useLast=False, baseOnly=False, \
																			stripExt=False, useActor=False ):
	"""
	Check theFigure or theActor for customData 'MultiPose#nn' keys matching the specified frame.
	If both theFigure and theActor are None, default to the currently selected scene actor.
	If useLast is set, return the customData 'MultiPose' if 'MultiPose#nn' is absent for that frame.
	Return the customData value (or None if not found) and which key was located.
	
	theFigure	The figure, if any selected for saving
	theActor	In the absence of a selected figure, the actor whose customData 'MultiPose' is to be returned
	theFrame	The frame component of the 'MultiPose#nn' customData key being searched for. If None, default to 
				the current scene frame
	useLast		Allows the 'MultiPose' customData to be returned if frame specific version is absent
	baseOnly	Remove the path component and return only the basename
	stripExt	Remove the '.pz2' or other extension if True
	useActor	If theFigure is not None, try theActor before falling back to theFigure. (Single recursion)	
	"""
	global CustomDataMultiPoseKey
	
	return GetFrameCustomData( theFigure, theActor, CustomDataMultiPoseKey, theFrame, useLast, baseOnly, stripExt, useActor )

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
	global CustomDataPoseNameKey
	
	return GetFrameCustomData( theFigure, theActor, CustomDataPoseNameKey, theFrame, useLast, baseOnly, stripExt, useActor )

def GetCustomDataKeys( theObject ):
	"""
	Given theObject, which may refer to either a figure or an actor, return a list of keys for which customData exists.
	
	theObject	the entity (figure or actor) whose list of customData keys are to be returned.
	"""
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global PoserPythonMethod
	global PPM_ALLCUSTOMDATA
	
	if PoserPythonMethod[ PPM_ALLCUSTOMDATA ]: # Manual CustomData key recording not required
		keys = list( ( theObject.AllCustomData() or {} ).keys() )
	else:
		customKeys = theObject.CustomData( CustomDataListKey )
		keys = []
		if customKeys is not None: # Extract existing customData Keys value into keys list
			keys = customKeys.split( CustomDataKeyDelimiter )
	return keys

def SetCustomDataKeys( theObject, keys ):
	"""
	Given theObject, which may refer to either a figure or an actor, set the CustomDataListKey customData to the 
	concatenated, delimited list of keys specified. This is redundant if the AllCustomData() method is available.
	
	theObject	the entity (figure or actor) whose list of customData keys is to be set.
	keys		the list of keys to be concatenated and delimited then saved to CustomDataListKey.
	"""
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global PoserPythonMethod
	global PPM_ALLCUSTOMDATA
	
	if not PoserPythonMethod[ PPM_ALLCUSTOMDATA ] and len( keys ) > 0:
		customKeys = CustomDataKeyDelimiter.join( keys )
		theObject.SetCustomData( CustomDataListKey, customKeys, 0, 0 ) # Save lookup for customData Keys

def AddCustomData( theObject, key, value=None, storeWithPoses=0, storeWithMaterials=0 ):
	"""
	Given theObject, which may refer to either a figure or an actor, set its customData as specified.
	The key will be included in the CustomDataListKey value, delimited by CustomDataKeyDelimiter: ';'
	Separate key storage is not required in Poser 12.0.735 with the AllCustomData() method.
	
	theObject			the entity (figure or actor) whose customData is to be set.
	key					the key whose customData value is to be set.
	value				the customData value associated with key.
	storeWithPoses		flag 0 or 1 indicating whether Poser will save the customData with poses.
	storeWithMaterials	flag 0 or 1 indicating whether Poser will save the customData with material poses.
	"""	
	global PoserPythonMethod
	global PPM_ALLCUSTOMDATA
	
	if theObject and key:
		if not PoserPythonMethod[ PPM_ALLCUSTOMDATA ]: # Separate key storage required.
			keys = GetCustomDataKeys( theObject )
			if key not in keys:
				keys.append( key )
				SetCustomDataKeys( theObject, keys ) # Record the newly added key
		theObject.SetCustomData( key, value, storeWithPoses, storeWithMaterials )
	
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
	global CustomDataExpressionKey
	global CustomDataLocationKey
	global CustomDataPoseNameKey
	global CustomDataPoseNameFrameFmt
	
	if len( theData ) > 0: # Need to maintain customData Keys list
		keys = GetCustomDataKeys( theObject )
		for (key, data) in iter( theData.items() ):
			if key not in keys: # Avoid duplicating existing keys
				keys.append( key )
			theObject.SetCustomData( key, data.value, data.storeWithPoses, data.storeWithMaterials )
			if key in [ CustomDataExpressionKey, CustomDataLocationKey, CustomDataPoseNameKey ]: # Replicate this customData for the current frame
				framekey = CustomDataPoseNameFrameFmt.format( key, CustomDataFrameDelimiter, poser.Scene().Frame() )
				if framekey not in keys:
					keys.append( framekey )
				theObject.SetCustomData( framekey, data.value, data.storeWithPoses, data.storeWithMaterials )
		SetCustomDataKeys( theObject, keys )

def StringSplitByNumbers(x):
	"""
	Regular expression sort key for numeric order sorting of digit sequences in alphanumeric strings
	Credit: Matt Connolly (http://code.activestate.com/recipes/users/4177092/)
	"""
	r = re.compile('(\d+)')
	l = r.split(x)
	return [int(y) if y.isdigit() else y for y in l]

def ListCustomData( theObject ):
	"""
	Print a list of all customData for theObject, with frame references numerically sorted
	Excludes the CustomDataListKey itself, which is only there to provide missing customData lookup functionality
	
	theObject:	figure or actor type scene object. If None, report customData for the entire scene
	"""
	global CustomDataListKey
	global CustomDataKeyDelimiter
	global CustomDataFrameDelimiter
	global CustomDataPoseNameKey
	global CustomDataPoseNameFrameFmt
	
	customKeys = GetCustomDataKeys( theObject )
	if customKeys:
		keyList = sorted( customKeys, key = StringSplitByNumbers )
		keyList = [ elem for elem in keyList if elem != CustomDataListKey ]
		for key in keyList:
			data = theObject.CustomData( key )
			print( '{}, "{}" {}'.format( theObject.Name(), key, json.dumps( data ) ) )

def ListAllCustomData( theObject=None ):
	"""
	Print a list of all customData for theObject, or the entire scene, with frame references numerically sorted
	Excludes the CustomDataListKey itself, which is only there to provide missing customData lookup functionality
	
	theObject:	figure or actor type scene object. If None, report customData for the entire scene
	"""	
	if theObject is not None:
		ListCustomData( theObject )
	else:
		scene = poser.Scene()
		for actor in scene.Actors(): # This parses all unparented actors in the scene as well as actors in figures.
			ListCustomData( actor )
		else:
			for figure in scene.Figures():
				ListCustomData( figure )


# Override Poser 11.2 AppVersion() method format change
if len( poser.AppVersion().split( '.' ) ) < 4:
	oldav = poser.AppVersion
	newav = poser.AppVersion()

	def AppV():
		"""
		For Poser versions prior to 11.2, poser.AppVersion() returns 'a.b.c .build' as the version string.
		For Poser versions after 11.3, poser.AppVersion() returns 'a.b.build' where the build sequence restarted at zero.
		PoserUI replaces poser.AppVersion() with a new variant, returning 'a.b.0.build' and adding offsets of 40000 for
		Poser 11.3 and 41000 for Poser 12 to the build number to maintain its sequence for scripts which make build value
		comparison.
		The original poser.AppVersion() function is available as PoserUI.oldav(), if required.
		"""
		global newav
	
		v = newav.split( '.' )
		v[ 1 ] = v[ 1 ].strip()
		v[ 2 ] = str( int( v[ 2 ] ) + 29000 + ( int( v[ 0 ] ) * 1000 ) ) # v11 -> 40000, v12 -> 41000
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
		print( '   {} : {}'.format( pref, prefs.preferences[ pref ] ) )
	print( 'UnitScaleFactor = {}'.format( UnitScaleFactor ) )
	print( 'UnitScaleType = {}'.format( UnitTypeName[ UnitScaleType ] ) )
	print( 'UseCompression = {}'.format( UseCompression ) )

### END ###