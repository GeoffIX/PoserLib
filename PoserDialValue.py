# -*- coding: utf-8 -*- 
# PoserDialValue.py
# (c) 2014-2020 an0malaus (Geoff Hicks/GeoffIX)
# 
# This module provides a function to determine (as accurately as possible) the actual dial setting
# of a Poser parameter value. Initial attempts to reverse the affects of ERC influence included in
# the parameter.Value() output were limited to linear regression. It is still not possible to fully
# account for the effect of parameter limit applied discontinuities in the inverse ERC function,
# but the recent exposure to python of parameter ValueOperations() has improved the situation greatly.
# As a consequence of the need to interpolate cubic and higher equations, numpy, scipy.interpolate
# and collections modules must be imported. Scipy is slightly problematic as it is not currently
# bundled with Python 2.7 libraries as used internally by Poser Pro 2014 and thus must be installed
# manually within Poser's python bundle. Note also that the quadratic spline interpolation (3 points)
# is not an accurate replication of Poser's interpolation which is currently undocumented.
# 
# Using SciPy with Poser Python 2.7
# 
# Procedure to allow PoserPro2012 on OS X to use SciPy python package for spline interpolation
# As determined by GeoffIX (Geoff Hicks) 15th November 2012
# 
# *** WARNING: NOT FOR THE FAINT OF HEART ***
# 
# Since SciPy relies on NumPy, the version of SciPy must be compiled against a compatible version of NumPy.
# Unfortunately, the NumPy bundled with PoserPro2012 is too old to support the latest builds of SciPy that
# work with the Python 2.7 installation bundled with PoserPro2012 and Mac OSX 10.7/8.
# 
# Thus both SciPy and NumPy packages compatible with Python 2.7 need to be built and installed in Mac OS X's
# /Library/Python/2.7/site-packages/ folder
# 
# Once that's done, we need to tell PoserPro2012 to use our newer version of NumPy and the SciPy package
# 
# Python has several mechanisms to help it locate packages. The relevant one for this operation is the .pth file.
# Poser Python will also locate packages contained within a folder named for the package and containing an __init__.py
# file.
# 
# Within the PoserPro2012 Application (Show Package Contents in the Finder) go to Contents/Resources/site-packages
# 
# In here you will find a 'numpy' folder with PoserPro2012's bundled numpy package version 1.5.1 or so. This folder
# will need to be renamed ( to oldnumpy or somesuch ) or its existence will override the numpy.pth file we will create.
# 
# Create a text file named scipy.pth with the content: (pointing to where you've installed the new scipy module)
# /Library/Python/2.7/site-package/scipy
# 
# Create a text file named numpy.pth with the content: (pointing to where you've installed the new numpy module)
# /Library/Python/2.7/site-package/numpy
# 
# NOTE:
# Every time you install an update to PoserPro2012, you will need to check whether a replacement numpy folder has been
# created in /Applications/Poser Pro 2012/Poser Pro 2012/Contents/Resources/site-packages to replace the one you
# renamed to oldnumpy and remove it. The installation process does not seem to remove any extraneous files, so the
# numpy.pth and scipy.pth added previously should remain untouched.
#
# v1.0	20140603	Initial module version
# v1.1	20140605	Sudden realisation that the ValueOperation exposure allows all ERC influence to be recorded,
#					then removed, allowing the uninfluenced dial value to be determined, before re-instatement.
#		20140723	Implemented valueOperation removal and re-creation to avoid interpolation failure when
#					limits are forced. set "remove" flag to False (defaults to True) for interpolated method.
#					Added ListValueOperations() method for Python Shell debugging.
# v1.2	20140916	Extracted and exposed RemoveValueOperations() and RestoreValueOperations() from DialValue()
#					to allow extra-modular control of parameters without ValueOperation influence.
# v1.3	20141022	Removed reliance on numpy, scipy and collections.
# v1.4	20150123	Provided method to determine dial values for a range of frames without having to remove and
#					re-apply value operations at each frame.
#					Added exception handling to RemoveValueOperations to help debug Poser crashes in calls to
#					DeleteValueOperation().
# v1.5	20150713	Most crashes appear to occur when the value operations are corrupted by defining a channel
#					dependency before the channel has been created during loading, resulting in SourceParameter()
#					returning None. Since DeleteValueOperation() crashes Poser back to the OS when attempting to 
#					remove such corrupted items before python gets a chance to handle any error, the solutions are
#					to extract forward reference value operations until after both actors have been loaded and their
#					channels created (not a problem within a figure's own actors - Poser copes with this), and to
#					pre-test the value operation's SourceParameter() is not None and skip deletion if it is.
# v1.6	20150720	Improve debugging output at point where an exception will be raised by SourceParameter() None.
#					Added FigureName() method to protect against attribute exceptions if Figure is None.
# v1.7	20150805	Added DialAnimation() method returning interpolation and continuity and keyframe status as well 
#					as values for a specified range of frames.
#					Import namedtuple from collections for easy keyframe tuple field extraction
# v1.8	20160527	Use new P11.0.4 build 32467 parameter method UnaffectedValue() when available instead of deleting
#					and recreating parameter value operations for the dial value at a single frame. Unfortunately,
#					no UnaffectedValueFrame() method is available to get the dial values at frames other than the 
#					current frame, so DialValueFrames and DialAnimation still remove and reapply value operations.
# v1.9	20160908	Still no UnaffectedValueFrame() in P11.0.5 build 32974, but have DialValueFrames and DialAnimation
#					test for operation on a single frame and use UnaffectedValue() to avoid removing valueOperations.
#					Fix RestoreValueOperations() which seems to be using a 1 based KeyValueOp index rather than 0.
#					Fix ListValueOperations() which also incorrectly uses a 1 base GetKey() index.
#					Fix LogValueOperations() which also incorrectly uses a 1 base GetKey() index.
# v2.0	20201103	Replace print statement with function for Python 3 compatibility in Poser 12.
#					Python3 raise only takes a single Exception instance or class with explicit parameters.
########################################################################################################################
from __future__ import print_function

poserDialValueVersion = "2.0"
POSER_DIALVALUE_VERSION = "POSERDIALVALUE_VERSION"
debug = False
remove = True
indent = ' '*4
limitEachValOp = False # Apply parameter Min & Max limits (if enabled) at every valueOperation evaluation if True

import poser
#import numpy as np
#from scipy.interpolate import interp1d
from collections import OrderedDict, namedtuple

# Ease lookup of keyframe attributes
KeyFrame = namedtuple( 'KeyFrame', [ 'frame', 'value', 'const', 'linear', 'spline', 'sbreak', 'haskey' ] )

valOpTypeNames = { \
					poser.kValueOpTypeCodeDELTAADD : "valueOpDeltaAdd", \
					poser.kValueOpTypeCodeDIVIDEBY : "valueOpDivideBy", \
					poser.kValueOpTypeCodeDIVIDEINTO : "valueOpDivideInto", \
					poser.kValueOpTypeCodeKEY : "valueOpKey", \
					poser.kValueOpTypeCodeMINUS : "valueOpMinus", \
					poser.kValueOpTypeCodePLUS : "valueOpPlus", \
					poser.kValueOpTypeCodePYTHONCALLBACK : "valueOpPythonCallBack", \
					poser.kValueOpTypeCodeTIMES : "valueOpTimes" \
				 }

def ApplyParmLimits( theParm, theValue ):
	"""
	This method returns a value conforming to the limits inherent in the specified parameter.
	The value returned is unchanged from that specified if the parameter does not enforce it's limits.
	
	theParm		: The parameter whose limits are to be applied, if enforced.
	theValue	: the value to be modified and returned.
	"""
	if theParm.ForceLimits():
		return max(theParm.MinValue(), min(theParm.MaxValue(), theValue))
	else:
		return theValue

def Plural( theCount ):
	"""
	This method returns a string containing the English plural suffix appropriate for the specified integer.
	E.G.	>>> print( "{} hop{}, {} skip{} and {} jump{}".format( 0, Plural(0), 1, Plural(1), 2, Plural(2) ) )
	E.G.	>>> 0 hops, 1 skip and 2 jumps
	
	theCount	: the integer whose English plural suffix ( "" or "s" ) is to be returned.
	"""
	if theCount == 1:
		return ""
	else:
		return "s"

def FigureName(theFigure, internal=False):
	"""
	This method returns the external or internal name of theFigure or '_NO_FIG_' if None
	
	theFigure	: the figure whose external or internal name is to be returned
	internal	: (optional) boolean indicating the internal name is to be returned. Defaults to external name.
	"""
	if theFigure:
		if internal:
			return theFigure.InternalName()
		else:
			return theFigure.Name()
	else:
		return "_NO_FIG_"

def ListValueOperations(theParm):
	"""
	This method prints a list of the value operations for the specified parameter for debugging purposes.
	
	theParm		: the parameter whose value operations are to be printed.
	"""
	try:
		print( "{}DialValue: {}, {} has {:d} value operation{}; Value() = {:0g} Unaffected Value() = {:0g}".format( \
							indent*1, \
							theParm.Actor().InternalName(), theParm.InternalName(), theParm.NumValueOperations(), \
							Plural( theParm.NumValueOperations() ), theParm.Value(), theParm.UnaffectedValue())  )
	except:
		print( "{}DialValue: {}, {} has {:d} value operation{}; Value() = {:0g}".format( indent*1, \
							theParm.Actor().InternalName(), theParm.InternalName(), theParm.NumValueOperations(), \
							Plural( theParm.NumValueOperations() ), theParm.Value())  )
	if theParm.NumValueOperations() > 0:
		for theValOp in theParm.ValueOperations():
			if theValOp.Type() == poser.kValueOpTypeCodePYTHONCALLBACK:
				print( "{}Python CallBack Value Operation".format( indent*2 ) )
			else:
				srcParm = theValOp.SourceParameter()
				if srcParm:
					print( "{}{}\n{}{}\n{}{}\n{}{}".format( indent*2, valOpTypeNames[ theValOp.Type() ], \
									indent*3, FigureName( theValOp.SourceParameter().Actor().ItsFigure() ), \
									indent*3, theValOp.SourceParameter().Actor().InternalName(), \
									indent*3, theValOp.SourceParameter().InternalName() ) )
					if theValOp.Type() == poser.kValueOpTypeCodeDELTAADD:
						print( "{}deltaAddDelta {:0.6f}".format( indent*2, theValOp.Delta() ) )
					elif theValOp.Type() == poser.kValueOpTypeCodeKEY:
						print( "{}beginValueKeys".format( indent*3 ) )
						#for theKeyIndex in range(1, theValOp.NumKeys() + 1): # Complete BS! index should be 0 based.
						for theKeyIndex in range( theValOp.NumKeys() ):
							(theKey, theValue) = theValOp.GetKey( theKeyIndex )
							print( "{}valueKey {:0g} {:0g}".format( indent*4, theKey, theValue ) )
						print( "{}endValueKeys".format( indent*3 ) )
				else:
					print( "***WARNING***{}{} SourceParameter is None".format( indent*2, \
																			valOpTypeNames[ theValOp.Type() ] ) )

def LogValueOperations(logFile, theParm):
	"""
	This method logs a list of the value operations for the specified parameter for debugging purposes.
	Returns True if no problems were found with the parameter's value operations and False otherwise.
	
	logFile		: the previously opened log file to which value operations are to be logged.
	theParm		: the parameter whose value operations are to be logged.
	"""
	logFile.write( "{}{}, {} has {:d} value operation{}\n".format( indent*1, \
							theParm.Actor().InternalName(), theParm.InternalName(), theParm.NumValueOperations(), \
																		Plural( theParm.NumValueOperations() ) ) )
	if theParm.NumValueOperations() > 0:
		for theValOp in theParm.ValueOperations():
			if theValOp.Type() == poser.kValueOpTypeCodePYTHONCALLBACK:
				logFile.write( "{}Python CallBack Value Operation\n".format( indent*2 ) )
			else:
				srcParm = theValOp.SourceParameter()
				if srcParm:
					logFile.write( "{}{}\n{}{}\n{}{}\n{}{}\n".format( indent*2, valOpTypeNames[ theValOp.Type() ], \
									indent*3, FigureName( theValOp.SourceParameter().Actor().ItsFigure() ), \
									indent*3, theValOp.SourceParameter().Actor().InternalName(), \
									indent*3, theValOp.SourceParameter().InternalName() ) )
					if theValOp.Type() == poser.kValueOpTypeCodeDELTAADD:
						logFile.write( "{}deltaAddDelta {:0.6f}\n".format( indent*2, theValOp.Delta() ) )
					elif theValOp.Type() == poser.kValueOpTypeCodeKEY:
						logFile.write( "{}beginValueKeys\n".format( indent*3 ) )
						#for theKeyIndex in range(1, theValOp.NumKeys() + 1): # Utter garbage! Use 0 based index
						for theKeyIndex in range( theValOp.NumKeys() ):
							(theKey, theValue) = theValOp.GetKey( theKeyIndex )
							logFile.write( "{}valueKey {:0g} {:0g}\n".format( indent*4, theKey, theValue ) )
						logFile.write( "{}endValueKeys\n".format( indent*3 ) )
				else:
					logFile.write( "***WARNING***{}{} SourceParameter is None\n".format( indent*2, \
																			valOpTypeNames[ theValOp.Type() ] ) )
					return False
	return True

def RemoveValueOperations( theParm ):
	"""
	This method will remove all value operations except python callbacks from the specified parameter and
	return them as a list (including the python callbacks, if any).
	
	theParm		: the parameter whose value operations are to be removed and returned.
	"""
	theValOps = theParm.ValueOperations()
	valOpIndex = 0
	if theParm.NumValueOperations() > 0: # Protect zip operation from extra-modular calls with theValOps == None
		for ( valOpIndex, theValOp ) in zip( range( theParm.NumValueOperations() - 1, -1, -1 ), theValOps ):
			if theValOp.Type() == poser.kValueOpTypeCodePYTHONCALLBACK: # Ignore python callbacks
				continue
			if theValOp.SourceParameter() is not None: # Prevent crash on deletion if None
				try: # NOTE: Poser will still crash if deleting a valOp with no source parameter
					success = theParm.DeleteValueOperation( valOpIndex )
				except:
					raise Exception( "PoserError: Failed in {}.DeleteValueOperation( {} )".format( \
																			theParm.InternalName(), valOpIndex ) )
				if debug:
					print( "{}Success ({:d}) deleting Value Operation Index {:d}".format( indent*2, \
																							success, valOpIndex ) )
			else: # Should try to Remove corrupted value operation from the list returned and continue
				raise Exception( "PoserError: {} {} {}.SourceParameter() is None ( {} )".format( \
										FigureName( theParm.Actor().ItsFigure() ), theParm.Actor().InternalName(), \
																				theParm.InternalName(), valOpIndex ) )
	return theValOps

def RestoreValueOperations( theParm, theValOps ):
	"""
	This method will restore the listed value operations excepting python callbacks to the specified parameter.
	
	theParm		: the parameter whose value operations are to be restored.
	theValOps	: the list of value operations to be restored.
	"""
	if theValOps is not None: # Protect extra-modular calls from iteration over 'NoneType' object
		for theValOp in theValOps:
			if theValOp.Type() == poser.kValueOpTypeCodePYTHONCALLBACK: # Ignore python callbacks
				if debug:
					print( "{}Existing Python CallBack ignored.".format( indent*1 ) )
			else:
				newValOp = theParm.AddValueOperation( theValOp.Type(), theValOp.SourceParameter() )
				if theValOp.Type() == poser.kValueOpTypeCodeDELTAADD:
					newValOp.SetDelta( theValOp.Delta() )
				elif theValOp.Type() == poser.kValueOpTypeCodeKEY:
					#for theKeyIndex in range( 1, theValOp.NumKeys() + 1 ): # This doesn't seem right - 0 based?
					for theKeyIndex in range( theValOp.NumKeys() ):
						( theKey, theValue ) = theValOp.GetKey( theKeyIndex )
						newValOp.InsertKey( theKey, theValue )

def DialValue( theParm ):
	"""
	This method returns the dial setting of the specified parameter excluding any valueOperation influence.
	NOTE: If the PoserDialValue.remove global is True, value operations for the parameter will be removed
			and restored to avoid their influence when the parameter value is determined.
	NOTE: 	Python callbacks are not removed as they cannot be re-instated.
	NOTE: If the PoserDialValue.remove global is False, interpolation will be attempted to determine the 
			dial value distinct from value operation influence.
	NOTE: 	Interpolation may fail if limits are applied or if inverse functions are unbounded/undefined.
	
	theParm		: the parameter whose dial setting (rather than value) is to be returned.
	"""
	try:
		return theParm.UnaffectedValue()
	except:
		pass
	if debug:
		ListValueOperations( theParm )
	if theParm.NumValueOperations() > 0:
		if remove: # Delete all non-Python ValueOperations, record dial value then re-create ValueOperations.
			theValOps = RemoveValueOperations( theParm )
			if debug:
				print( "{}Removed existing Value Operations. Value() = {:0g}".format( indent*1, theParm.Value() ) )
				ListValueOperations( theParm )
			theDialValue = theParm.Value()
			if debug:
				print( "{}Restoring {:d} deleted Value Operation{}".format( indent*1, len( theValOps ), \
																			Plural( len( theValOps ) ) ) )
			RestoreValueOperations( theParm, theValOps )
			if debug:
				print( "{}Restored deleted Value Operations.".format( indent*1 ) )
				ListValueOperations( theParm )
			return theDialValue
		else: # Original interpolation method
			"""
			theDialValue = theParm.Value() # Attempt to extract Dial value from value Operation influences
			theValOps = theParm.ValueOperations()
			theValOps.reverse() # Start with the current Value() and work backwards through the value Operations
			for theValOp in theValOps:
				theValOpType = theValOp.Type()
				if theValOpType == poser.kValueOpTypeCodePYTHONCALLBACK: # Ignore python callbacks
					if debug:
						print( "{}DialValue: Python CallBack of {}, {} ignored.".format(indent*1, \
								theParm.Actor().InternalName(), theParm.InternalName()) )
					continue
				try:
					theSourceParm = theValOp.SourceParameter()
					#theSourceActor = theSourceParm.Actor()
					#theSourceFigure = theSourceActor.ItsFigure()
					# Here we won't ignore the influence of value operations from other figures
					theSourceValue = theSourceParm.Value()
					if theValOpType == poser.kValueOpTypeCodeDELTAADD:
						theDialValue -= theValOp.Delta() * theSourceValue
					elif theValOpType == poser.kValueOpTypeCodeKEY:
						valOpKeys = []
						valOpValues = []
						minKeyIndex = -1
						maxKeyIndex = -1
						for k in range(theValOp.NumKeys()):
							#(key, val) = theValOp.GetKey(k + 1) # Again, No! Must be zero based index
							(key, val) = theValOp.GetKey(k)
							valOpKeys.append(key)
							valOpValues.append(val)
							if minKeyIndex < 0: # Haven't found smallest key yet
								minKeyIndex = k
								minKeyValue = key
							elif key < minKeyValue: # New smallest key
								minKeyIndex = k
								minKeyValue = key
							if maxKeyIndex < 0:
								maxKeyIndex = k
								maxKeyValue = key
							elif key > maxKeyValue:
								maxKeyIndex = k
								maxKeyValue = key
						splineKeys = np.array(valOpKeys)
						splineVals = np.array(valOpValues)
						order = theValOp.NumKeys() - 1
						if order < 1:
							if order == 0: # Single Key, Value pair - Constant Extrapolation
								splineValue = valOpValues[0]
							else: # No Key, Value pairs - Zero Extrapolation
								splineValue = 0.0
						else:
							if order >= 3:
								splineFunc = interp1d(splineKeys, splineVals, kind='cubic')
							elif order == 2: # NOTE: This is not an accurate replication of Poser's interpolation
								splineFunc = interp1d(splineKeys, splineVals, kind='quadratic')
							elif order == 1:
								splineFunc = interp1d(splineKeys, splineVals, kind='linear')
							if theSourceValue < minKeyValue: # Tests to avoid range error on splineFunc
								splineValue = splineVals[minKeyIndex]
							elif theSourceValue > maxKeyValue:
								splineValue = splineVals[maxKeyIndex]
							else:
								splineValue = splineFunc(theSourceValue)
						theDialValue -= splineValue
					elif theValOpType == poser.kValueOpTypeCodePLUS:
						theDialValue -= theSourceValue
					elif theValOpType == poser.kValueOpTypeCodeMINUS:
						theDialValue += theSourceValue
					elif theValOpType == poser.kValueOpTypeCodeTIMES:
						# If the source value is zero, we cannot divide to determine the dial value, so give up
						if theSourceValue == 0.0:
							return theParm.Value()
						else:
							theDialValue /= theSourceValue
					elif theValOpType == poser.kValueOpTypeCodeDIVIDEBY:
						theDialValue *= theSourceValue
					elif theValOpType == poser.kValueOpTypeCodeDIVIDEINTO:
						if theDialValue == 0.0: # Can't divide by zero, so give up
							return theParm.Value()
						else:
							theDialValue = theSourceValue / theDialValue
					else:
						if debug:
							print( "else: Figure {}, Actor {}, Parameter {} has a problem with this valueOperation.".format( \
									theParm.Actor().ItsFigure().Name(), theParm.Actor().InternalName(), \
									theParm.InternalName()) )
						continue
					if debug:
						if theValOpType == poser.kValueOpTypeCodeDELTAADD:
							print( "{}DialValue: {}, {} source: {}, {} {} ({:f}) Delta: {:f} = {:f}".format(indent*2, \
									theParm.Actor().InternalName(), theParm.InternalName(), \
									theSourceParm.Actor().InternalName(), theSourceParm.InternalName(), \
									valOpTypeNames[theValOpType], theSourceValue, theValOp.Delta(), \
									theSourceValue * theValOp.Delta()) )
						elif theValOpType == poser.kValueOpTypeCodeKEY:
							print( "{}DialValue: {}, {} source: {}, {} {} ({:f}) Value: {:f}".format(indent*2, \
									theParm.Actor().InternalName(), theParm.InternalName(), \
									theSourceParm.Actor().InternalName(), theSourceParm.InternalName(), \
									valOpTypeNames[theValOpType], theSourceValue, splineValue) )
						else:
							print( "{}DialValue: {}, {} source: {}, {} {} ({:f})".format(indent*2, \
									theParm.Actor().InternalName(), theParm.InternalName(), \
									theSourceParm.Actor().InternalName(), theSourceParm.InternalName(), \
									valOpTypeNames[theValOpType], theSourceValue) )
				except: # Should never happen unless error in Poser source file so ignore.
					if debug:
						print( "WARNING: Figure {}, Actor {}, Parameter {} has a problem with this valueOperation.".format( \
									theParm.Actor().ItsFigure().Name(), theParm.Actor().InternalName(), \
									theParm.InternalName()) )
					continue
				if limitEachValOp: # Apply parameter limits (if forced) at each value operation.
					if debug:
						preLimitValue = theDialValue
					theDialValue = ApplyParmLimits(theParm, theDialValue)
					if debug:
						print( "{}DialValue: {}, {} {:f} (Limited: {:f})".format(indent*2, \
									theParm.Actor().InternalName(), theParm.InternalName(), \
									preLimitValue, theDialValue) )
			if debug:
				print( "{}DialValue of {}, {} is {:f} (Limited: {:f})".format(indent*1, \
									theParm.Actor().InternalName(), theParm.InternalName(), \
									theDialValue, ApplyParmLimits(theParm, theDialValue)) )
			"""
			return ApplyParmLimits(theParm, theDialValue)
	else: # No valueOp influence
		return theParm.Value()

def DialValueFrames( theParm, firstFrame, lastFrame ):
	"""
	This method returns a list of the dial settings of the specified parameter within a specified range of frames, 
	excluding any valueOperation influence.
	NOTE: If the PoserDialValue.remove global is ignored. Value operations for the parameter will be removed
			and restored to avoid their influence while the parameter's values are being determined.
	NOTE: 	Python callbacks are not removed as they cannot be re-instated.
	NOTE: Removal and reinstatement of value operations is minimised when compared to iterating calls to 
			DialValue() over multiple frames.
	NOTE: If a single frame value is sought and the UnaffectedValue() method is available, it will be used.
	
	theParm		: the parameter whose dial setting (rather than value) is to be returned.
	firstFrame	: the first frame (zero based) at which the parameter's dial setting is to be returned.
	lastFrame	: the last frame (zero based) at which the parameter's dial setting is to be returned.
	"""
	theValues = []
	if lastFrame == firstFrame: # Only one frame, so we can avoid slow iterations over the frame range
		try:
			scene = poser.Scene()
			frame = scene.Frame()
			if frame != firstFrame:
				scene.SetFrame( firstFrame )
			theValues.append( theParm.UnaffectedValue() )
			if frame != firstFrame:
				scene.SetFrame( frame )
			return theValues
		except: # Assume no UnaffectedValue() method available
			pass
	if debug:
		ListValueOperations( theParm )
	if theParm.NumValueOperations() > 0:
		if remove: # Delete all non-Python ValueOperations, record dial value then re-create ValueOperations.
			theValOps = RemoveValueOperations( theParm )
			if debug:
				print( "{}Removed existing Value Operations. Value() = {:0g}".format( indent*1, theParm.Value() ) )
				ListValueOperations( theParm )
			for frame in range( firstFrame, lastFrame + 1 ):
				theValues.append( theParm.ValueFrame( frame ) )
			if debug:
				print( "{}Restoring {:d} deleted Value Operation{}".format( indent*1, len( theValOps ), \
																			Plural( len( theValOps ) ) ) )
			RestoreValueOperations( theParm, theValOps )
			if debug:
				print( "{}Restored deleted Value Operations.".format( indent*1 ) )
				ListValueOperations( theParm )
		else: # Original interpolation method
			for frame in range( firstFrame, lastFrame + 1 ):
				theValues.append( theParm.ValueFrame( frame ) )
	else: # No valueOp influence
		for frame in range( firstFrame, lastFrame + 1 ):
			theValues.append( theParm.ValueFrame( frame ) )
	return theValues

def DialAnimation( theParm, firstFrame, lastFrame ):
	"""
	This method returns a list of tuples containing the dial setting, interpolation, continuity and keyframe state 
	of the specified parameter within a specified range of frames, excluding any valueOperation influence.
	NOTE: If the PoserDialValue.remove global is ignored. Value operations for the parameter will be removed
			and restored to avoid their influence while the parameter's values are being determined.
	NOTE: 	Python callbacks are not removed as they cannot be re-instated.
	NOTE: Removal and reinstatement of value operations is minimised when compared to iterating calls to 
			DialValue() over multiple frames.
	NOTE: The returned list items are KeyFrame namedtuples ( value, const, linear, spline, sbreak, haskey )
	NOTE: If a single frame value is sought and the UnaffectedValue() method is available, it will be used.
	
	theParm		: the parameter whose dial setting (rather than value) is to be returned.
	firstFrame	: the first frame (zero based) at which the parameter's dial setting is to be returned.
	lastFrame	: the last frame (zero based) at which the parameter's dial setting is to be returned.
	"""
	theKeyFrames = []
	if lastFrame == firstFrame: # Only one frame, so we can avoid slow iterations over the frame range
		try:
			scene = poser.Scene()
			frame = scene.Frame()
			if frame != firstFrame:
				scene.SetFrame( firstFrame )
			theKeyFrames.append( KeyFrame( firstFrame, theParm.UnaffectedValue(), \
												theParm.ConstantAtFrame( firstFrame ), \
												theParm.LinearAtFrame( firstFrame ), \
												theParm.SplineAtFrame( firstFrame ), \
												theParm.SplineBreakAtFrame( firstFrame ), \
												theParm.HasKeyAtFrame( firstFrame ) ) )
			if frame != firstFrame:
				scene.SetFrame( frame )
			return theKeyFrames
		except:
			pass
	if debug:
		ListValueOperations( theParm )
	if theParm.NumValueOperations() > 0:
		if remove: # Delete all non-Python ValueOperations, record dial value then re-create ValueOperations.
			theValOps = RemoveValueOperations( theParm )
			if debug:
				print( "{}Removed existing Value Operations. Value() = {:0g}".format( indent*1, theParm.Value() ) )
				ListValueOperations( theParm )
			for frame in range( firstFrame, lastFrame + 1 ):
				theKeyFrames.append( KeyFrame( frame, theParm.ValueFrame( frame ), \
												theParm.ConstantAtFrame( frame ), \
												theParm.LinearAtFrame( frame ), \
												theParm.SplineAtFrame( frame ), \
												theParm.SplineBreakAtFrame( frame ), \
												theParm.HasKeyAtFrame( frame ) ) )
			if debug:
				print( "{}Restoring {:d} deleted Value Operation{}".format( indent*1, len( theValOps ), \
																			Plural( len( theValOps ) ) ) )
			RestoreValueOperations( theParm, theValOps )
			if debug:
				print( "{}Restored deleted Value Operations.".format( indent*1 ) )
				ListValueOperations( theParm )
		else: # Original interpolation method
			for frame in range( firstFrame, lastFrame + 1 ):
				theKeyFrames.append( KeyFrame( frame, theParm.ValueFrame( frame ), \
												theParm.ConstantAtFrame( frame ), \
												theParm.LinearAtFrame( frame ), \
												theParm.SplineAtFrame( frame ), \
												theParm.SplineBreakAtFrame( frame ), \
												theParm.HasKeyAtFrame( frame ) ) )
	else: # No valueOp influence
		for frame in range( firstFrame, lastFrame + 1 ):
			theKeyFrames.append( KeyFrame( frame, theParm.ValueFrame( frame ), \
											theParm.ConstantAtFrame( frame ), \
											theParm.LinearAtFrame( frame ), \
											theParm.SplineAtFrame( frame ), \
											theParm.SplineBreakAtFrame( frame ), \
											theParm.HasKeyAtFrame( frame ) ) )
	return theKeyFrames

#"""