# Contributing to YT Automation

Thank you for your interest in contributing. Here is how to get involved.

## Reporting bugs

Open an issue and include:
- Your OS and Python version
- The full error message from your terminal
- Which step failed (script, voiceover, footage, assembly, upload)

## Suggesting features

Open an issue with the label `enhancement`. Describe what you want and why it would be useful.

## Submitting code

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test it by running `python main.py` with a topic
5. Commit: `git commit -m "Add: brief description of change"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request against `main`

## Code style

- Keep each module focused on one responsibility
- Add a comment above any non-obvious logic
- Do not hardcode API keys — always use `config.py` and `.env`
- Test on Windows before submitting

## Areas that need help

- Django web UI wrapper
- Thumbnail auto-generation
- TikTok / Instagram Reels cross-posting
- Subtitle/caption overlay on video
- Topic queue and scheduling system
