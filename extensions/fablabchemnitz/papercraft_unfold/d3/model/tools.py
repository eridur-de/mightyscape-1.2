import os
from importlib import import_module

from . import formats
from .formats import *
from .basemodel import ModelParser, Exporter

from types import ModuleType

supported_formats = []

class ModelType:
    """Represents a type of coding of 3D object, and the module enabling
    parsing and exporting
    """
    def __init__(self, typename, inner_module):
        """Creates a ModelType

        :param typename: the name of the 3D format
        :param inner_module: the module that will parse and export the format
        """
        self.typename = typename
        self.inner_module = inner_module

    def test_type(self, file):
        """Tests if a file has the correct type

        :param file: path to the file to test
        """
        return getattr(self.inner_module, 'is_' + self.typename)(file)

    def create_parser(self, *args, **kwargs):
        """Creates a parser of the current type
        """
        return getattr(self.inner_module, self.typename.upper() + 'Parser')(*args, **kwargs)

    def create_exporter(self, *args, **kwargs):
        """Creates an exporter of the current type
        """
        return getattr(self.inner_module, self.typename.upper() + 'Exporter')(*args, **kwargs)

def find_type(filename, supported_formats):
    """Find the correct type from a filename

    :param filename: path to the file
    :param supported_formats: list of formats that we have modules for
    """
    for type in supported_formats:
        if type.test_type(filename):
            return type

for name in formats.__dict__:
    if isinstance(formats.__dict__[name], ModuleType) and name != 'glob':
        type = ModelType(name, formats.__dict__[name])
        supported_formats.append(type)

def load_model(path, up_conversion = None):
    """Loads a model from a path

    :param path: path to the file to load
    :param up_conversion: conversion of up vectors
    """
    parser = None
    type = find_type(path, supported_formats)

    if type is None:
        raise Exception("File format not supported \"" + str(type) + "\"")

    parser = type.create_parser(up_conversion)
    parser.parse_file(path)

    return parser

def export_model(model, path):
    """Exports a model to a path

    :param model: model to export
    :param path: path to save the model
    """
    exporter = None
    type = find_type(path, supported_formats)

    if type is None:
        raise Exception('File format is not supported')

    exporter = type.create_exporter(model)
    return exporter

def convert(input, output, up_conversion = None):
    """Converts a model

    :param input: path of the input model
    :param output: path to the output
    :param up_conversion: convert the up vector
    """
    model = load_model(input, up_conversion)
    exporter = export_model(model, output)
    return str(exporter)

