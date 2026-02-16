# VHS tape for resumake short demo (LinkedIn-friendly)
# Run: vhs demo-short.tape

Output demo-short.gif

Set Shell "zsh"
Set FontSize 14
Set Width 900
Set Height 520
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set CursorBlink false

# Prepare: work in a clean temp dir
Hide
Type "source ~/.zshrc 2>/dev/null; cd $(mktemp -d) && clear"
Enter
Sleep 500ms
Show

# --- Scaffold ---
Sleep 200ms
Type "resumake init my-cv"
Enter
Sleep 1200ms

Type "cd my-cv"
Enter
Sleep 300ms

# --- Build English CV ---
Type "resumake build --lang en --no-open"
Enter
Sleep 1500ms

# --- Browse themes ---
Type "resumake themes"
Enter
Sleep 1500ms

# --- Build with a different theme ---
Type "resumake build --theme modern --no-open"
Enter
Sleep 1500ms

# --- Validate ---
Type "resumake validate"
Enter
Sleep 1200ms

# --- Export to Markdown ---
Type "resumake export md --no-open"
Enter
Sleep 1200ms

# --- Show available commands ---
Type "resumake --help"
Enter
Sleep 2s

Sleep 300ms
