import io
import sys
from contextlib import contextmanager
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import difflib
import json
import xml.etree.ElementTree as ET
import re

#// Converting to a Python executable shit
class FprgToPythonConverter:
    def __init__(self):
        self.indent_level = 0
        self.in_function = False
        self.current_function = ""
        self.variables = set()
    
    def indent(self):
        return "    " * self.indent_level
    
    def parse_expression(self, expr):
        if expr is None or expr == "":
            return ""
        if isinstance(expr, ET.Element):
            expr = expr.text if expr.text else ""
        expr = str(expr)
        expr = expr.replace("&amp;", "and")
        expr = expr.replace("&", "and")
        expr = expr.replace("|", "or")
        expr = expr.replace("≠", "!=")
        expr = expr.replace("≤", "<=")
        expr = expr.replace("≥", ">=")
        expr = re.sub(r"ToStr\((.*?)\)", r"str(\1)", expr)
        expr = re.sub(r"ToInt\((.*?)\)", r"int(\1)", expr)
        expr = re.sub(r"ToFloat\((.*?)\)", r"float(\1)", expr)
        return expr
    
    def convert_node(self, node):
        if node.tag == "function":
            return self.convert_function(node)
        elif node.tag == "declare":
            return self.convert_declare(node)
        elif node.tag == "assign":
            return self.convert_assign(node)
        elif node.tag == "input":
            return self.convert_input(node)
        elif node.tag == "output":
            return self.convert_output(node)
        elif node.tag == "if":
            return self.convert_if(node)
        elif node.tag == "while":
            return self.convert_while(node)
        elif node.tag == "for":
            return self.convert_for(node)
        elif node.tag == "return":
            return self.convert_return(node)
        elif node.tag == "call":
            return self.convert_call(node)
        return ""

    def convert_function(self, node):
        name = node.attrib.get('name', 'Main')
        self.current_function = name
        self.in_function = True
        
        params = []
        params_node = node.find(".//parameters")
        if params_node is not None:
            for param in params_node.findall("parameter"):
                params.append(param.attrib.get('name', ''))
        
        python_code = f"\ndef {name}({', '.join(params)}):\n"
        self.indent_level += 1
        
        body = node.find(".//body")
        if body is not None:
            for child in body:
                python_code += self.convert_node(child)
        
        self.indent_level -= 1
        self.in_function = False
        return python_code

    def convert_declare(self, node):
        vars_str = node.attrib.get('name', '')
        vars_list = [v.strip() for v in vars_str.split(',')]
        self.variables.update(vars_list)
        
        #// Initialize variables to None or 0 based on type
        var_type = node.attrib.get('type', 'Integer')
        init_value = "0" if var_type in ['Integer', 'Real'] else "''"
        
        return ''.join(f"{self.indent()}{var} = {init_value}\n" for var in vars_list)

    def convert_assign(self, node):
        var = node.attrib.get('variable', '')
        expr = self.parse_expression(node.attrib.get('expression', ''))
        return f"{self.indent()}{var} = {expr}\n"

    def convert_input(self, node):
        var = node.attrib.get('variable', '')
        prompt = node.attrib.get('prompt', '')
        
        var_type = "int"  #// Default to int for now
        if prompt:
            return f"{self.indent()}{var} = {var_type}(input({prompt}))\n"
        else:
            return f"{self.indent()}{var} = {var_type}(input())\n"

    def convert_output(self, node):
        expr = self.parse_expression(node.attrib.get('expression', ''))
        newline = node.attrib.get('newline', 'True').lower() == 'true'
        end = "\\n" if newline else ""
        return f"{self.indent()}print({expr}, end='{end}')\n"

    def convert_for(self, node):
        var = node.attrib.get('variable', '')
        start = node.attrib.get('start', '0')
        end = node.attrib.get('end', '0')
        step = node.attrib.get('step', '1')
        direction = node.attrib.get('direction', 'inc')
        
        #// Adjust the range based on direction
        
        if direction == 'inc':
            python_code = f"{self.indent()}for {var} in range({start}, {end} + 1, {step}):\n"
        else:
            python_code = f"{self.indent()}for {var} in range({start}, {end} - 1, -{step}):\n"
        
        self.indent_level += 1
        for child in node:
            python_code += self.convert_node(child)
        self.indent_level -= 1
        
        return python_code

    def convert_if(self, node):
        condition = self.parse_expression(node.find("condition"))
        python_code = f"{self.indent()}if {condition}:\n"
        
        self.indent_level += 1
        then_node = node.find("then")
        if then_node is not None:
            for child in then_node:
                python_code += self.convert_node(child)
        self.indent_level -= 1
        
        else_node = node.find("else")
        if else_node is not None and len(else_node) > 0:
            python_code += f"{self.indent()}else:\n"
            self.indent_level += 1
            for child in else_node:
                python_code += self.convert_node(child)
            self.indent_level -= 1
            
        return python_code

    def convert_file(self, fprg_file):
        try:
            tree = ET.parse(fprg_file)
            root = tree.getroot()
            
            python_code = "# Generated Python code from Flowgorithm\n\n"
            
            #// Find all functions, including those directly in the root
            functions = root.findall(".//function")
            if not functions:
                print("Warning: No functions found in the file")
                return None
                
            for function in functions:
                python_code += self.convert_node(function)
            
            if "Main" in python_code:
                python_code += "\nif __name__ == '__main__':\n    Main()\n"
                
            return python_code
        except Exception as e:
            print(f"Error converting file: {e}")
            raise

#// The Test Case and Result Classes
@dataclass
class TestCase:
    inputs: List[str]
    expected_output: str
    description: str = ""
    
@dataclass
class TestResult:
    passed: bool
    actual_output: str
    expected_output: str
    diff: str
    error: str = ""

#// Test function family
class SeminarWorkTester:
    def __init__(self, converter):
        self.converter = converter
        
    @contextmanager
    def capture_output(self):
        new_out = io.StringIO()
        old_out = sys.stdout
        old_in = sys.stdin
        try:
            sys.stdout = new_out
            yield new_out
        finally:
            sys.stdout = old_out
            sys.stdin = old_in
            
    def provide_input(self, inputs: List[str]):
        return io.StringIO('\n'.join(inputs))
    
    def compare_output(self, actual: str, expected: str) -> Tuple[bool, str]:
        actual = actual.strip().replace('\r\n', '\n')
        expected = expected.strip().replace('\r\n', '\n')
        
        if actual == expected:
            return True, ""
            
        diff = difflib.unified_diff(
            expected.splitlines(True),
            actual.splitlines(True),
            fromfile='expected',
            tofile='actual'
        )
        return False, ''.join(diff)
    
    def test_submission(self, fprg_file: str, test_cases: List[TestCase]) -> Dict[str, TestResult]:
        results = {}
        
        try:
            python_code = self.converter.convert_file(fprg_file)
            namespace = {}
            exec(python_code, namespace)
            
            for i, test_case in enumerate(test_cases):
                test_name = f"test_case_{i+1}"
                if test_case.description:
                    test_name = f"{test_name}_{test_case.description}"
                
                try:
                    with self.capture_output() as output:
                        sys.stdin = self.provide_input(test_case.inputs)
                        
                        if 'Main' in namespace:
                            namespace['Main']()
                        
                    actual_output = output.getvalue()
                    passed, diff = self.compare_output(actual_output, test_case.expected_output)
                    
                    results[test_name] = TestResult(
                        passed=passed,
                        actual_output=actual_output,
                        expected_output=test_case.expected_output,
                        diff=diff
                    )
                except Exception as e:
                    results[test_name] = TestResult(
                        passed=False,
                        actual_output="",
                        expected_output=test_case.expected_output,
                        diff="",
                        error=str(e)
                    )
                    
        except Exception as e:
            results["conversion_error"] = TestResult(
                passed=False,
                actual_output="",
                expected_output="",
                diff="",
                error=f"Failed to convert or execute code: {str(e)}"
            )
            
        return results
    
    def generate_report(self, results: Dict[str, TestResult], format: str = 'text') -> str:
        if format == 'json':
            return json.dumps({
                k: {
                    'passed': v.passed,
                    'actual_output': v.actual_output,
                    'expected_output': v.expected_output,
                    'diff': v.diff,
                    'error': v.error
                } for k, v in results.items()
            }, indent=2)
            
        report = []
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.passed)
        
        report.append("=== Seminar Work Test Results ===")
        report.append(f"Passed: {passed_tests}/{total_tests} tests\n")
        
        for test_name, result in results.items():
            report.append(f"Test: {test_name}")
            report.append(f"Status: {'PASSED' if result.passed else 'FAILED'}")
            
            if not result.passed:
                if result.error:
                    report.append(f"Error: {result.error}")
                else:
                    report.append("Differences found:")
                    report.append(result.diff)
            report.append("")
            
        return '\n'.join(report)