# Static Analysis Issue Log

The initial analysis was run before the fixes with Pylint 4.1.3, Bandit 1.9.4,
and Flake8 7.4.1. The repository's assigned file is
`loan_calculator.py` (the handout refers to `inventory_system.py`).

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| FTP transport | Security (Bandit B402/B321, high) | 3, 68-71 | Plain FTP can expose credentials and reports in transit. | Replaced FTP with an HTTPS connection and made credentials required caller inputs. |
| Unsafe deserialization | Security (Bandit B302, medium) | 64 | `marshal.loads` can execute unsafe serialized data. | Replaced marshal with validated JSON loading. |
| Hard-coded password / malformed parameter | Security and syntax | 67 | The password default was exposed, and the placeholder made the file invalid Python. | Removed the default and require a password argument. |
| Mutable default argument | Bug (Pylint W0102) | 20 | `history=[]` is shared by every call, so old loan types leak into later calls. | Changed it to `None` and initialize/use history only when supplied. |
| Predictable application IDs | Security (Bandit B311, low) | 51 | `random.randint` is predictable for identifiers. | Used `secrets.randbelow` for an unpredictable ID. |
| Unclosed files | Reliability (Pylint R1732) | 55, 63, 70 | Manual `open`/`close` calls can leak resources if an operation fails. | Used context managers or `Path.read_bytes`. |
| Incorrect maximum-loan calculation | Logic bug | 33-38 | The rate was unused and the function summed the same amount once per month instead of converting an affordable EMI to principal. | Applied the standard present-value formula, including a zero-rate case. |
| Unused import and style violations | Style (Flake8 F401/E302/E501/F541) | 2, 14-106 | Unused `math`, missing blank lines, long lines, and an f-string without interpolation reduced readability. | Removed the import, formatted functions and calls, and replaced the unnecessary f-string. |

## Verification

After the fixes:

```text
Pylint: 10.00/10
Bandit: No issues identified
Flake8: no output
```

