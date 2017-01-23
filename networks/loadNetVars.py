import numpy
import tensorflow as tf
import util.settings as s
from util.utils import easy_scope

def _fixModelPath(path):
    # Ensures that sloppily constructed model paths still work
    if not path.endswith(".npz"):
        return path + ".npz"
    else:
        return path

def extractLayers(scope, weightsPath, biasesPath, device="/cpu:0"):
    """
    Function that extracts weights and biases into properly scoped variables.
    
    Positional arguments:
    scope -- tf.VariableScope ( or string representing a scope ) to place variables in
    weightsPath -- path to .npz file containing the weights
    biasesPath -- path to .npz file containing the biases

    Keyword arguments:
    device -- device on which to place the created variables
    """

    # Loads parameters from .npz files, one for the weights and another for the biases
    # Assumes that the proper variable names exist in the given scope somewhere
    weightsPath = _fixModelPath(weightsPath)
    biasesPath = _fixModelPath(biasesPath)

    # Raw numpy values.  Need to be loaded into variables.
    weightsDict = numpy.load(weightsPath)
    biasesDict = numpy.load(biasesPath)

    # Here, we do a for loop looping through all of the names, "name".
    with tf.device(device) as dev:
        with easy_scope(scope) as model_scope:
            for name, weights_tnsr in weightsDict.iteritems():    
                if name.startswith("/"):
                    name = name[1:]
                if name.endswith("/"):
                    name = name[:-1]
                with easy_scope(name) as layer_scope:
                    tf.get_variable("Weights", trainable=False, initializer=tf.constant(weights_tnsr))
                    tf.get_variable("Bias", trainable=False, initializer=tf.constant(biasesDict[name]))
    return
