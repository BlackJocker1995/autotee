#!/usr/bin/env python3
"""
Test script for LinkJava2Rust tool implementation
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from LLM.tools.language_tools import LinkJava2Rust

def test_link_java2rust():
    """Test the LinkJava2Rust tool with sample data"""
    
    # Create an instance of the tool
    project_root = os.path.dirname(os.path.abspath(__file__))
    tool = LinkJava2Rust(project_root_path=project_root)
    
    # Test case 1: Simple function with int parameters (similar to original hash function)
    print("=== Test Case 1: Simple function with int parameters ===")
    result1 = tool._run(
        function_name="add",
        arguments={"a": "int", "b": "int"},
        return_type="int"
    )
    print(result1[:500] + "..." if len(result1) > 500 else result1)
    print("\n" + "="*50 + "\n")
    
    # Test case 2: Function with byte array parameter
    print("=== Test Case 2: Function with byte array parameter ===")
    result2 = tool._run(
        function_name="hash",
        arguments={"input": "byte[]", "seed": "int"},
        return_type="int"
    )
    print(result2[:500] + "..." if len(result2) > 500 else result2)
    print("\n" + "="*50 + "\n")
    
    # Test case 3: Function with String parameter
    print("=== Test Case 3: Function with String parameter ===")
    result3 = tool._run(
        function_name="process",
        arguments={"text": "String", "count": "int"},
        return_type="String"
    )
    print(result3[:500] + "..." if len(result3) > 500 else result3)

if __name__ == "__main__":
    test_link_java2rust()