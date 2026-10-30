import pytest
from app.services.code_executor import code_executor, CodeExecutionRequest, TestCase

@pytest.mark.asyncio
async def test_python_code_execution_success():
    req = CodeExecutionRequest(
        code='print("Hello World from Execution Sandbox")',
        language='python'
    )
    res = await code_executor.execute_code(req)
    assert res.status == 'success'
    assert res.exit_code == 0
    assert "Hello World from Execution Sandbox" in res.stdout

@pytest.mark.asyncio
async def test_python_code_execution_error():
    req = CodeExecutionRequest(
        code='raise ValueError("Intentional execution error")',
        language='python'
    )
    res = await code_executor.execute_code(req)
    assert res.status == 'error'
    assert res.exit_code != 0
    assert "ValueError" in res.stderr

@pytest.mark.asyncio
async def test_python_security_violation_prohibited_module():
    req = CodeExecutionRequest(
        code='import os\nprint(os.listdir("."))',
        language='python'
    )
    res = await code_executor.execute_code(req)
    assert res.status == 'security_violation'
    assert "Security Restriction" in res.stderr
    assert "os" in res.stderr

@pytest.mark.asyncio
async def test_python_security_violation_eval():
    req = CodeExecutionRequest(
        code='eval("2 + 2")',
        language='python'
    )
    res = await code_executor.execute_code(req)
    assert res.status == 'security_violation'
    assert "eval" in res.stderr

@pytest.mark.asyncio
async def test_python_test_cases_verification():
    req = CodeExecutionRequest(
        code='def add(a, b): return a + b\nprint(f"Result: {add(2, 3)}")',
        language='python',
        test_cases=[
            TestCase(name="Test 1", expected_output="Result: 5"),
            TestCase(name="Test 2", expected_output="Result: 10")
        ]
    )
    res = await code_executor.execute_code(req)
    assert res.status == 'success'
    assert len(res.test_results) == 2
    assert res.test_results[0].passed is True
    assert res.test_results[1].passed is False
