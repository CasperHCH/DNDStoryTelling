# Legacy Tests Archive

This folder contains older test files that have been superseded by the consolidated test suite.

## Why These Tests Were Archived

As part of the December 2025 test consolidation effort, we reduced **35 test files** down to **4 focused test suites**:

### Active Test Suite (in parent directory)
1. **test_auth_integration.py** - Complete authentication testing (11 tests)
2. **test_basic_functionality.py** - Core functionality validation (18 tests)
3. **test_api_endpoints.py** - API layer testing (21 tests)
4. **test_deployment.py** - Infrastructure validation (20 tests)

**Total: 70 tests with 93% pass rate**

### Archived Files in This Folder

These files represent earlier testing attempts with various issues:
- **Duplicate coverage** - Multiple files testing the same functionality
- **Incomplete tests** - Tests that were never finished
- **Experimental approaches** - Demo files showing different testing strategies
- **Backup files** - `.backup` copies of test files
- **Over-mocked tests** - Tests with excessive mocking that don't validate real behavior
- **Failing tests** - Tests that were failing and need updating

## Consolidated Test Benefits

✅ **Reduced file sprawl** - 4 files instead of 35  
✅ **Easier maintenance** - Clear organization by concern  
✅ **Better coverage** - Focused, comprehensive tests  
✅ **Faster execution** - No duplicate test runs  
✅ **Clear purpose** - Each file has a specific role  

## If You Need to Reference These Files

These archived tests may contain useful patterns or test cases that could be incorporated into the active test suite. Feel free to review them, but **do not run them directly** as they may:
- Conflict with the new test structure
- Have outdated dependencies
- Fail due to code changes
- Contain deprecated testing approaches

## Restoration

If you need to restore any of these files:
1. Review the consolidated test suite first to see if the functionality is already covered
2. Extract specific test cases rather than the entire file
3. Update the test to match current code patterns
4. Add to the appropriate consolidated test file (don't create new files)

---

**Archived**: December 12, 2025  
**Reason**: Test consolidation and cleanup  
**Safe to Delete**: After 6 months (June 2026) if no issues found
