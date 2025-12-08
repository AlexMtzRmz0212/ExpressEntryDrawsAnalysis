from config import Config
from fetcher import Fetcher
from processor import Processor
from analyzer import Analyzer
from email_service import EmailService

class Manager:
    def __init__(self):
        self.config     = Config()
        self.fetcher    = Fetcher()
        self.processor  = Processor()
        self.analyzer   = Analyzer()
        self.email      = EmailService()