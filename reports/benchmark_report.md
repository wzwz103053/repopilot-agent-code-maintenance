# RepoPilot V14 Benchmark Report

## Summary

- Total cases: 1
- Success rate: 0.0%
- Test pass rate: 0.0%
- Patch apply rate: 0.0%
- Files-to-modify accuracy: 0.0%
- Modified-files accuracy: 0.0%
- Retrieval file recall: 0.0%
- Average repair attempts: 0.00
- Average elapsed seconds: 0.15

## Cases

| Case | Success | Test | Patch | Files to modify | Modified files | Retrieval recall | Repair attempts | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| demo_missing_user_profile | ❌ | ❌ | ❌ | 0.0% | 0.0% | 0.0% | 0 | 0.15 |

## Raw Metrics

```json
[
  {
    "case_id": "demo_missing_user_profile",
    "name": "Profile page should not crash for missing user",
    "success": false,
    "test_passed": false,
    "patch_applied": false,
    "guardrails_passed": true,
    "patch_safety_passed": false,
    "files_to_modify_accuracy": 0.0,
    "modified_files_accuracy": 0.0,
    "retrieval_file_recall": 0.0,
    "root_cause_file_hit": false,
    "repair_attempts": 0,
    "elapsed_seconds": 0.14525609998963773,
    "test_status": "unknown",
    "patch_status": "skipped",
    "final_summary": "RepoPilot stopped before applying the patch because patch safety guardrails blocked the generated diff.\n\nBlock reason:\nPatch diff is empty.\n\nFindings:\n- [block] unsafe_patch at patch: Patch diff is empty."
  }
]
```
