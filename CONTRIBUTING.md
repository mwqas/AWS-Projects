# Contributing

Start with a small issue describing a reproducible problem or learning improvement. Never include credentials, private customer details, or account-specific deployment files.

1. Make a branch for one change.
2. Preserve upstream attribution and licensing notices.
3. Explain code examples in plain language and label mock versus real AWS behavior.
4. Run the offline checks from the repository root:

```powershell
python -m unittest discover -s agentcore-customer-support/companion/offline -p "test_*.py" -v
python scripts/check_resources.py
```

For SDK changes, also run the reference tests in its locked dependency environment. Cloud results must identify the SDK versions and distinguish successful tool execution from fallback responses. Do not claim a cloud test based on a mock test.

Open a pull request describing the change, reason, and checks actually performed. Documentation changes should preserve working relative links. Editing book.md does not automatically regenerate the PDF; disclose any difference between editions.
