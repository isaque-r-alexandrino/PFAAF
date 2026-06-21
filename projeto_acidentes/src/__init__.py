"""
Pacote de análise de acidentes em rodovias federais
"""
from .data_generator import DataGenerator
from .data_processor import DataProcessor
from .visualizer import Visualizer
from .analyzer import Analyzer

__version__ = "2.0.0"
__all__ = ['DataGenerator', 'DataProcessor', 'Visualizer', 'Analyzer']