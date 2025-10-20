# Review Checklist for New Features

When reviewing a pull request that introduces a new feature, please verify the following items:

1. **Logging Coverage**  
   Ensure that all critical execution paths are covered by logging using the module located at `PyQtInspect._pqi_bundle.pqi_log`.
2. **Regression Risk**  
   Assess whether existing functionality is affected. If it is, inspect the related code line by line to surface potential bugs.
3. **Documentation Update**  
   Confirm that `README.md` has been updated as needed. If improvements are required, include suggested enhancements in the review comments along with an explicit diff.
