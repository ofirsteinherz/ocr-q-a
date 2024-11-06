# Makefile for Git operations

# Default target
.PHONY: commit init hard-reset

# Initialize a new Git repository and link it to a GitHub repository
init:
	@if [ -d ".git" ]; then \
		echo "Git repository already initialized."; \
	else \
		git init; \
		read -p "Enter the GitHub repository URL: " repo_url; \
		git remote add origin $$repo_url; \
		echo "Repository initialized and remote 'origin' set to $$repo_url."; \
	fi

# Commit changes to the main branch with a custom commit message
commit:
	@if [ -z "$(m)" ]; then \
		echo "Error: Please provide a commit message using 'make commit m=\"Your commit message\"'"; \
		exit 1; \
	fi
	git add .
	git commit -m "$(m)"
	git push origin main

# Hard reset the repository to the last pushed state, including ignored files
hard-reset:
	@git fetch origin
	@git reset --hard origin/main
	@git clean -fdx
