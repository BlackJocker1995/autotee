#!/usr/bin/env python3
"""
Test script for LinkJava2Rust tool implementation using pytest.
"""

import sys
import os
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from LLM.tools.language_tools import LinkJava2Rust

@pytest.fixture
def tool():
    """Fixture to create an instance of the LinkJava2Rust tool."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    return LinkJava2Rust(project_root_path=project_root)

def test_add_function(tool):
    """Test code generation for a simple 'add' function with int parameters."""
    result = tool._run(
        function_name="add",
        arguments={"a": "int", "b": "int"},
        return_type="int"
    )
    assert "public static int add(int a, int b)" in result
    assert "data: Option<i32>" in result
    assert "rust::add(params.a, params.b);" in result

def test_hash_function(tool):
    """Test code generation for a 'hash' function with a byte array parameter."""
    result = tool._run(
        function_name="hash",
        arguments={"input": "byte[]", "seed": "int"},
        return_type="int"
    )
    assert "public static int hash(byte[] input, int seed)" in result
    assert "JsonArray inputArray = new JsonArray();" in result
    assert "input: Vec<u8>" in result
    assert "rust::hash(params.input, params.seed);" in result

def test_process_function(tool):
    """Test code generation for a 'process' function with a String parameter."""
    result = tool._run(
        function_name="process",
        arguments={"text": "String", "count": "int"},
        return_type="String"
    )
    assert "public static String process(String text, int count)" in result
    assert "params.addProperty(\"text\", text);" in result
    assert "data: Option<String>" in result
    assert "text: String" in result
    assert "rust::process(params.text, params.count);" in result

def test_calculate_flags_function(tool):
    """Test code generation for a function with boolean and double parameters."""
    result = tool._run(
        function_name="calculate_flags",
        arguments={"is_active": "boolean", "threshold": "double"},
        return_type="boolean"
    )
    assert "public static boolean calculate_flags(boolean is_active, double threshold)" in result
    assert "params.addProperty(\"is_active\", is_active);" in result
    assert "params.addProperty(\"threshold\", threshold);" in result
    assert "data: Option<bool>" in result
    assert "is_active: bool" in result
    assert "threshold: f64" in result
    assert "rust::calculate_flags(params.is_active, params.threshold);" in result

def test_update_records_function(tool):
    """Test code generation for a function with long and float parameters."""
    result = tool._run(
        function_name="update_records",
        arguments={"record_id": "long", "value": "float"},
        return_type="long"
    )
    assert "public static long update_records(long record_id, float value)" in result
    assert "params.addProperty(\"record_id\", record_id);" in result
    assert "params.addProperty(\"value\", value);" in result
    assert "data: Option<i64>" in result
    assert "record_id: i64" in result
    assert "value: f32" in result
    assert "rust::update_records(params.record_id, params.value);" in result