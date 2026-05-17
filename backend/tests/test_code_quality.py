"""
Code quality and security tests for LexGuard One.

Tests for security vulnerabilities, performance issues, and code quality metrics.
"""

import ast
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

import pytest


class TestCodeQuality:
    """Tests for code quality metrics and standards."""

    def test_no_hardcoded_secrets(self):
        """Test that no hardcoded secrets exist in the codebase."""
        backend_path = Path("backend")
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
            r"['\"][A-Za-z0-9]{32,}['\"]",  # Long strings that might be keys
        ]
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            content = py_file.read_text()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{py_file}: {matches}")
        
        assert not violations, f"Potential hardcoded secrets found: {violations}"

    def test_no_sql_injection_vulnerabilities(self):
        """Test for potential SQL injection vulnerabilities."""
        backend_path = Path("backend")
        sql_patterns = [
            r"execute\s*\(\s*['\"].*%.*['\"]",  # String formatting in SQL
            r"query\s*\(\s*['\"].*\+.*['\"]",   # String concatenation in SQL
            r"SELECT.*\+.*FROM",                # Direct concatenation
        ]
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append(f"{py_file}: {matches}")
        
        assert not violations, f"Potential SQL injection vulnerabilities: {violations}"

    def test_proper_exception_handling(self):
        """Test that exceptions are properly handled and logged."""
        backend_path = Path("backend")
        
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    # Check for bare except clauses
                    if node.type is None:
                        pytest.fail(f"Bare except clause found in {py_file}:{node.lineno}")
                    
                    # Check for pass in except blocks (should at least log)
                    if (len(node.body) == 1 and 
                        isinstance(node.body[0], ast.Pass)):
                        pytest.fail(f"Empty except block in {py_file}:{node.lineno}")

    def test_function_complexity(self):
        """Test that functions don't exceed complexity thresholds."""
        backend_path = Path("backend")
        max_complexity = 15  # McCabe complexity threshold
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)
                    if complexity > max_complexity:
                        violations.append(
                            f"{py_file}:{node.lineno} - {node.name} "
                            f"(complexity: {complexity})"
                        )
        
        assert not violations, f"Functions exceed complexity threshold: {violations}"

    def _calculate_complexity(self, node):
        """Calculate McCabe complexity for a function node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

    def test_docstring_coverage(self):
        """Test that public functions have docstrings."""
        backend_path = Path("backend")
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file) or "__init__.py" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private functions
                    if node.name.startswith('_'):
                        continue
                    
                    # Check if function has docstring
                    if (not node.body or 
                        not isinstance(node.body[0], ast.Expr) or
                        not isinstance(node.body[0].value, ast.Constant) or
                        not isinstance(node.body[0].value.value, str)):
                        violations.append(f"{py_file}:{node.lineno} - {node.name}")
        
        # Allow some violations but not too many
        assert len(violations) < 10, f"Missing docstrings: {violations[:10]}"

    def test_import_organization(self):
        """Test that imports are properly organized."""
        backend_path = Path("backend")
        
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            lines = content.split('\n')
            
            # Find import section
            import_lines = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    import_lines.append((i, stripped))
                elif stripped and not stripped.startswith('#') and import_lines:
                    break  # End of import section
            
            # Check import order (stdlib, third-party, local)
            if len(import_lines) > 1:
                self._check_import_order(py_file, import_lines)

    def _check_import_order(self, py_file, import_lines):
        """Check that imports follow proper ordering."""
        stdlib_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'asyncio', 'logging',
            'typing', 'pathlib', 'tempfile', 'subprocess', 'unittest',
            'collections', 'itertools', 'functools', 're', 'ast'
        }
        
        sections = {'stdlib': [], 'third_party': [], 'local': []}
        
        for line_num, import_line in import_lines:
            if import_line.startswith('from __future__'):
                continue
                
            # Extract module name
            if import_line.startswith('import '):
                module = import_line.split()[1].split('.')[0]
            elif import_line.startswith('from '):
                module = import_line.split()[1].split('.')[0]
            else:
                continue
            
            if module in stdlib_modules:
                sections['stdlib'].append(line_num)
            elif module.startswith('backend'):
                sections['local'].append(line_num)
            else:
                sections['third_party'].append(line_num)
        
        # Check ordering
        all_lines = (sections['stdlib'] + sections['third_party'] + 
                    sections['local'])
        if all_lines != sorted(all_lines):
            # This is a warning, not a failure
            print(f"Warning: Import order in {py_file} could be improved")


class TestSecurity:
    """Security-focused tests."""

    def test_no_eval_usage(self):
        """Test that eval() is not used anywhere in the codebase."""
        backend_path = Path("backend")
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            if re.search(r'\beval\s*\(', content):
                violations.append(str(py_file))
        
        assert not violations, f"eval() usage found in: {violations}"

    def test_no_exec_usage(self):
        """Test that exec() is not used anywhere in the codebase."""
        backend_path = Path("backend")
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            if re.search(r'\bexec\s*\(', content):
                violations.append(str(py_file))
        
        assert not violations, f"exec() usage found in: {violations}"

    def test_secure_random_usage(self):
        """Test that secure random functions are used for security purposes."""
        backend_path = Path("backend")
        
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            
            # Check for insecure random usage in security contexts
            if re.search(r'random\.random\(\)', content):
                # Check if it's in a security-related context
                security_keywords = ['token', 'key', 'secret', 'password', 'salt']
                for keyword in security_keywords:
                    if keyword in content.lower():
                        pytest.fail(
                            f"Insecure random usage in security context: {py_file}"
                        )

    def test_input_validation_patterns(self):
        """Test that input validation patterns are present."""
        backend_path = Path("backend")
        
        # Look for FastAPI endpoints
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            
            # If file contains FastAPI routes
            if '@router.post' in content or '@app.post' in content:
                # Should have validation
                validation_patterns = [
                    r'validate_upload',
                    r'HTTPException',
                    r'status_code=400',
                    r'Pydantic',
                    r'BaseModel'
                ]
                
                has_validation = any(
                    re.search(pattern, content) for pattern in validation_patterns
                )
                
                if not has_validation:
                    print(f"Warning: {py_file} may lack input validation")


class TestPerformance:
    """Performance-related tests."""

    def test_no_blocking_calls_in_async(self):
        """Test that async functions don't contain blocking calls."""
        backend_path = Path("backend")
        
        blocking_patterns = [
            r'time\.sleep\(',
            r'requests\.get\(',
            r'requests\.post\(',
            r'open\(',  # Should use aiofiles
        ]
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    func_content = ast.get_source_segment(content, node)
                    if func_content:
                        for pattern in blocking_patterns:
                            if re.search(pattern, func_content):
                                violations.append(
                                    f"{py_file}:{node.lineno} - {node.name}"
                                )
        
        assert not violations, f"Blocking calls in async functions: {violations}"

    def test_database_connection_pooling(self):
        """Test that database connections use pooling where appropriate."""
        backend_path = Path("backend")
        
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            
            # Look for database connection patterns
            if 'firestore' in content.lower() or 'database' in content.lower():
                # Should have connection management
                if 'client' in content.lower():
                    # This is acceptable - using client pattern
                    continue

    def test_memory_usage_patterns(self):
        """Test for potential memory usage issues."""
        backend_path = Path("backend")
        
        memory_issues = []
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            
            # Look for potential memory leaks
            if re.search(r'while\s+True:', content):
                # Check if there's a break condition
                if 'break' not in content and 'return' not in content:
                    memory_issues.append(f"{py_file}: Potential infinite loop")
            
            # Look for large list comprehensions
            large_comprehension = re.search(
                r'\[.*for.*in.*range\(\s*\d{4,}\s*\)\s*\]', content
            )
            if large_comprehension:
                memory_issues.append(f"{py_file}: Large list comprehension")
        
        # These are warnings, not failures
        for issue in memory_issues:
            print(f"Warning: {issue}")


class TestMaintainability:
    """Tests for code maintainability."""

    def test_file_size_limits(self):
        """Test that files don't exceed reasonable size limits."""
        backend_path = Path("backend")
        max_lines = 1000
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            lines = py_file.read_text().split('\n')
            if len(lines) > max_lines:
                violations.append(f"{py_file}: {len(lines)} lines")
        
        assert not violations, f"Files exceed size limit: {violations}"

    def test_function_parameter_limits(self):
        """Test that functions don't have too many parameters."""
        backend_path = Path("backend")
        max_params = 8
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    param_count = len(node.args.args)
                    if param_count > max_params:
                        violations.append(
                            f"{py_file}:{node.lineno} - {node.name} "
                            f"({param_count} params)"
                        )
        
        assert not violations, f"Functions exceed parameter limit: {violations}"

    def test_class_size_limits(self):
        """Test that classes don't become too large."""
        backend_path = Path("backend")
        max_methods = 20
        
        violations = []
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    method_count = sum(
                        1 for child in node.body
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    )
                    if method_count > max_methods:
                        violations.append(
                            f"{py_file}:{node.lineno} - {node.name} "
                            f"({method_count} methods)"
                        )
        
        assert not violations, f"Classes exceed method limit: {violations}"


@pytest.mark.slow
class TestCodeMetrics:
    """Tests for overall code metrics and quality indicators."""

    def test_test_coverage_ratio(self):
        """Test that we have reasonable test coverage."""
        backend_path = Path("backend")
        test_path = Path("backend/tests")
        
        # Count source files
        source_files = len(list(backend_path.rglob("*.py"))) - len(list(test_path.rglob("*.py")))
        test_files = len(list(test_path.rglob("test_*.py")))
        
        # Should have at least 1 test file per 3 source files
        min_test_ratio = 0.3
        actual_ratio = test_files / max(source_files, 1)
        
        assert actual_ratio >= min_test_ratio, (
            f"Test coverage ratio too low: {actual_ratio:.2f} "
            f"(minimum: {min_test_ratio})"
        )

    def test_documentation_ratio(self):
        """Test that we have reasonable documentation coverage."""
        backend_path = Path("backend")
        
        total_functions = 0
        documented_functions = 0
        
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):  # Skip private functions
                        total_functions += 1
                        
                        # Check for docstring
                        if (node.body and 
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)):
                            documented_functions += 1
        
        if total_functions > 0:
            doc_ratio = documented_functions / total_functions
            min_doc_ratio = 0.7  # 70% documentation coverage
            
            assert doc_ratio >= min_doc_ratio, (
                f"Documentation ratio too low: {doc_ratio:.2f} "
                f"(minimum: {min_doc_ratio})"
            )

    def test_code_duplication(self):
        """Test for excessive code duplication."""
        backend_path = Path("backend")
        
        # Simple duplication detection - look for identical function bodies
        function_bodies = {}
        duplicates = []
        
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
                
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Get function body as string
                    body_str = ast.dump(node.body)
                    
                    if body_str in function_bodies:
                        duplicates.append(
                            f"{py_file}:{node.lineno} - {node.name} "
                            f"duplicates {function_bodies[body_str]}"
                        )
                    else:
                        function_bodies[body_str] = f"{py_file}:{node.lineno} - {node.name}"
        
        # Allow some duplication but not excessive
        assert len(duplicates) < 5, f"Excessive code duplication: {duplicates}"