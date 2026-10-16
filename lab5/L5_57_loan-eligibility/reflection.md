# Reflection

# Reflection Questions

## 1. Which issues were the easiest to fix, and which were the hardest? Why?

The easiest issues were the unused import, missing blank lines, long lines,
unnecessary f-string, and non-PEP 8 function names. These were localized style
changes with little effect on program behavior. The hardest issues were the
FTP replacement, unsafe serialization replacement, and maximum-loan
calculation. They required choosing safer alternatives, preserving the
program's behavior, and checking that the calculation used the interest rate
correctly. The original password placeholder also caused a syntax error, so it
had to be corrected before the program could be analyzed or executed.

## 2. Did the static analysis tools report any false positives? If so, describe one example.

The tools did not report a definite false positive in this exercise. The FTP
warnings were appropriate because plain FTP can expose credentials and report
data. The subprocess warnings were also reasonable because launching an
external command requires careful validation. However, a tool could flag an
apparently risky operation even when the surrounding application securely
controls its inputs. This demonstrates that static-analysis findings still
need to be reviewed in their application context rather than accepted
blindly.

## 3. How would you integrate static analysis tools into your actual software development workflow?

I would run Flake8 and Pylint locally before committing code and configure the
same checks in a pre-commit hook. Bandit would run on every pull request and
in the continuous-integration pipeline. The pipeline would fail for new high
or medium severity security findings and for code-quality errors, while
lower-priority warnings could be tracked for later cleanup. I would also keep
tool versions and configuration files in the repository so that every
developer and CI run uses consistent rules.

## 4. What tangible improvements did you observe in the code quality, readability, or potential robustness after applying the fixes?

The final code received a Pylint score of 10.00/10, Bandit reported no issues,
and Flake8 produced no violations. Readability improved through descriptive
snake_case names, type hints, docstrings, consistent formatting, and clearer
function structure. Robustness improved through context managers for files,
JSON instead of unsafe `marshal`, secure random identifiers, HTTPS instead of
FTP, explicit input checks, and a safe `main` guard. I also corrected the
maximum-loan formula and made the annual-rate convention consistent, which
improved the program's functional correctness in addition to its static
analysis results.
