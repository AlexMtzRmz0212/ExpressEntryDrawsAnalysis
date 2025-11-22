from config import Config
from data_fetcher import DataFetcher
from data_processor import DataProcessor
from data_analyzer import DataAnalyzer
from email_service import EmailService

class Manager:
    def __init__(self):
        self.config     = Config()
        self.fetcher    = DataFetcher()
        self.processor  = DataProcessor()
        self.analyzer   = DataAnalyzer()
        self.email      = EmailService()