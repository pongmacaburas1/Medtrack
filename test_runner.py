from django.test import TestCase
from django.test.runner import DiscoverRunner
from colorama import Fore, Style
import unittest

class CustomTestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        """
        Run the test suite and display colored output for test results.
        """
        result = unittest.TextTestRunner(verbosity=1, resultclass=ColoredTestResult).run(suite)
        
        return result

import re
def remove_parentheses(string):
    """
    Remove parentheses and their contents from a string.
    For example, "String (1ABC)" becomes "String" (trimming the terminal string).
    Using regex to match the pattern.
    """
    pattern = r'\s*\(.*?\)\s*'
    modified_string = re.sub(pattern, '', string)
    return modified_string.strip().upper()  # Convert to uppercase and remove leading/trailing spaces

class ColoredTestResult(unittest.TextTestResult):
    """
    Custom test result class to handle and display test results with colors.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []  # List to store test results and their colors

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"..\t{Fore.GREEN}OK{Style.RESET_ALL} \t {remove_parentheses(str(test))[:60]}\n")
        self.test_results.append((str(test), Fore.GREEN))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"..\t{Fore.RED}FAIL{Style.RESET_ALL} \t {remove_parentheses(str(test))[:60]}\n")
        self.test_results.append((str(test), Fore.RED))

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"..\t{Fore.YELLOW}ERROR{Style.RESET_ALL} \t {remove_parentheses(str(test))[:60]}\n")
        self.test_results.append((str(test), Fore.YELLOW))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.write(f"..\t{Fore.CYAN}SKIPPED{Style.RESET_ALL} t {remove_parentheses(str(test))[:60]}\n")
        self.test_results.append((str(test), Fore.YELLOW))


