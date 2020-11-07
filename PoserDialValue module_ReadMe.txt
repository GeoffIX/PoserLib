PoserDialValue:
This module provides a function to determine (as accurately as possible) the actual dial setting of a Poser parameter
value. Prior to Poser 11.0.4 build 32467, such information was not directly available to python. Initial attempts to
reverse the affects of ERC (valueOperations) influence included in the parameter.Value() output were limited to linear
regression. It is still not possible to fully account for the effect of parameter limit applied discontinuities in the
inverse ERC function, but the recent (2014) exposure to python of parameter ValueOperations() has improved the situation 
greatly. As a consequence of the need to interpolate cubic and higher order equations, numpy, scipy.interpolate and
collections modules must be imported. Scipy is slightly problematic as it is not currently bundled with Python 2.7
libraries as used internally by Poser Pro 2014 and thus must be installed manually within Poser's python bundle. Note
also that the quadratic spline interpolation (3 points) is not an accurate replication of Poser's interpolation which is
currently undocumented.

This version (2.0) of PoserDialValue no longer relies on the installation of additional modules outside PoserLib for its
functions, instead, relying on the current built-in UnaffectedValue() method for single frames, and the removal and
restoration of value operations to reveal the underlying dial values for a range of frames or animation sequence. One
potential drawback of this is that Python Callback routines are a valid valueOperation type. Unfortunately, so far in
Poser 11.3, there is no mechanism allowing the restoration of such a valueOperation, since the associated python script
is not exposed to the Python API.

Print statements have been replaced with function calls for Python 3 compatibility in Poser 12.

PoserDialValue Constants:

poserDialValueVersion, POSER_DIALVALUE_VERSION, debug, remove, indent, limitEachValOp
KeyFrame (a namedtuple to ease lookup of keyframe attributes)
valOpTypeNames (a dict mapping poser valueOp constants to text names)

PoserDialValue Methods:

def ApplyParmLimits( theParm, theValue ):
	"""
	This method returns a value conforming to the limits inherent in the specified parameter.
	The value returned is unchanged from that specified if the parameter does not enforce it's limits.
	
	theParm		: The parameter whose limits are to be applied, if enforced.
	theValue	: the value to be modified and returned.
	"""

def Plural( theCount ):
	"""
	This method returns a string containing the English plural suffix appropriate for the specified integer.
	E.G.	>>> print "{} hop{}, {} skip{} and {} jump{}".format( 0, Plural(0), 1, Plural(1), 2, Plural(2) )
	E.G.	>>> 0 hops, 1 skip and 2 jumps
	
	theCount	: the integer whose English plural suffix ( "" or "s" ) is to be returned.
	"""

def FigureName(theFigure, internal=False):
	"""
	This method returns the external or internal name of theFigure or '_NO_FIG_' if None
	
	theFigure	: the figure whose external or internal name is to be returned
	internal	: (optional) boolean indicating the internal name is to be returned. Defaults to external name.
	"""

def ListValueOperations(theParm):
	"""
	This method prints a list of the value operations for the specified parameter for debugging purposes.
	
	theParm		: the parameter whose value operations are to be printed.
	"""

def LogValueOperations(logFile, theParm):
	"""
	This method logs a list of the value operations for the specified parameter for debugging purposes.
	Returns True if no problems were found with the parameter's value operations and False otherwise.
	
	logFile		: the previously opened log file to which value operations are to be logged.
	theParm		: the parameter whose value operations are to be logged.
	"""

def RemoveValueOperations( theParm ):
	"""
	This method will remove all value operations except python callbacks from the specified parameter and
	return them as a list (including the python callbacks, if any).
	
	theParm		: the parameter whose value operations are to be removed and returned.
	"""

def RestoreValueOperations( theParm, theValOps ):
	"""
	This method will restore the listed value operations excepting python callbacks to the specified parameter.
	
	theParm		: the parameter whose value operations are to be restored.
	theValOps	: the list of value operations to be restored.
	"""

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

