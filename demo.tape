# VHS tape for resumake demo GIF
# Run: vhs demo.tape

Output demo.gif

Set Shell "zsh"
Set FontSize 14
Set Width 900
Set Height 520
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms
Set CursorBlink false

# Prepare: work in a clean temp dir with a sample job description
Hide
Type "source ~/.zshrc 2>/dev/null; cd $(mktemp -d) && clear"
Enter
Sleep 500ms
Show

# --- Scaffold ---
Sleep 300ms
Type "resumake init my-cv"
Enter
Sleep 2s

Type "cd my-cv"
Enter
Sleep 500ms

# --- Build English CV ---
Type "resumake build --lang en --no-open"
Enter
Sleep 3s

# --- Browse themes ---
Type "resumake themes"
Enter
Sleep 3s

# --- Build with a different theme ---
Type "resumake build --theme modern --no-open"
Enter
Sleep 3s

# --- Template variant: single-column layout ---
Type "resumake build --theme single-column --no-open"
Enter
Sleep 3s

# --- Validate ---
Type "resumake validate"
Enter
Sleep 2s

# --- Export to Markdown ---
Type "resumake export md --no-open"
Enter
Sleep 2s

# --- Export to JSON Resume ---
Type "resumake export jsonresume --no-open"
Enter
Sleep 2s

# --- Export to HTML ---
Type "resumake export html --no-open"
Enter
Sleep 2s

# --- Create a job description for AI features ---
Hide
Type "cat > job.txt << 'EOF'"
Enter
Type "Senior Software Engineer - TechCorp"
Enter
Type "We are looking for an experienced engineer with Python, React, and cloud infrastructure skills."
Enter
Type "Requirements: 5+ years experience, microservices, CI/CD, team leadership."
Enter
Type "EOF"
Enter
Sleep 500ms
Type "clear"
Enter
Sleep 500ms
Show

# --- AI: Content suggestions ---
Type "resumake suggest"
Enter
Sleep 12s

# --- AI: ATS keyword analysis ---
Type "resumake ats job.txt"
Enter
Sleep 12s

# --- AI: Tailor CV for a job ---
Type "resumake tailor job.txt --no-open"
Enter
Sleep 12s

# --- AI: Cover letter ---
Type "resumake cover job.txt --no-open"
Enter
Sleep 12s

# --- Show available commands ---
Type "resumake --help"
Enter
Sleep 4s

Sleep 1s
