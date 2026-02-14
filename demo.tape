# VHS tape for resumake demo GIF
# Run: vhs demo.tape

Output demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 900
Set Height 520
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms
Set CursorBlink false

# Prepare: work in a clean temp dir
Hide
Type "cd $(mktemp -d) && clear"
Enter
Sleep 500ms
Show

# Scaffold a new project
Sleep 300ms
Type "resumake init my-cv"
Enter
Sleep 2s

# Enter the project
Type "cd my-cv"
Enter
Sleep 500ms

# Build an English CV
Type "resumake build --lang en --no-open"
Enter
Sleep 3s

# List available themes
Type "resumake themes"
Enter
Sleep 3s

# Build with a different theme
Type "resumake build --lang en --theme modern --no-open"
Enter
Sleep 3s

Sleep 1s
