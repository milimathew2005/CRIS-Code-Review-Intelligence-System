# Contributing to CRIS

First off, thank you for taking the time to contribute! Contributions are what make the open source community such an amazing place to learn, inspire, and create.

---

## Code of Conduct

This project and everyone participating in it is governed by the [CRIS Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### Reporting Bugs
- Check the issues tab to see if the bug has already been reported.
- If it hasn't, open a new issue. Include clear steps to reproduce, expected vs actual behavior, and relevant logs or stack traces.

### Suggesting Enhancements
- Open an enhancement suggestion issue.
- Describe the feature, why it is valuable, and how it aligns with the project goals.

### Code Contributions (Pull Requests)
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```
2. Set up the development environment (refer to the [Setup Guide](README.md#setup--installation)).
3. Make your changes. Ensure the codebase remains clean and well-documented.
4. Run the automated test suite before submitting:
   ```bash
   pytest backend/tests/
   ```
   All tests must pass.
5. Commit your changes following descriptive messaging:
   ```bash
   git commit -m "feat: add AST support for decorator declarations"
   ```
6. Push to your branch and open a Pull Request targeting `main`.

---

## Code Style & Standards

- **Python**: Follow PEP 8 guidelines. Write clear docstrings for all functions, services, and schemas.
- **FastAPI**: Declare explicit response schemas and utilize dependency injection (`Depends`) for resources.
- **Streamlit**: Decouple layout views from business/database queries by querying the REST backend.
- **Testing**: Add assertions for boundary exceptions, mock network calls where appropriate, and keep fixtures modular.
