import sys

# Read the file
with open('/Users/berntblankholm/efmd-gap-tool/frontend/app.py', 'r') as f:
    lines = f.readlines()

# Find and fix the corrupted section (lines 98-106, 0-indexed so 97-105)
# Remove the cat command lines and replace with proper code
fixed_lines = []
skip_until = -1

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Skip the corrupted section (lines 99-106)
    if line_num >= 99 and line_num <= 106:
        if line_num == 99:
            # Replace with the correct code
            fixed_lines.append("        programmes = db_service.list_programmes()\n")
        # Skip all other corrupted lines
        continue
    else
cat > fix_app.py << 'ENDFILE'
import sys

# Read the file
with open('/Users/berntblankholm/efmd-gap-tool/frontend/app.py', 'r') as f:
    lines = f.readlines()

# Find and fix the corrupted section (lines 98-106, 0-indexed so 97-105)
# Remove the cat command lines and replace with proper code
fixed_lines = []
skip_until = -1

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Skip the corrupted section (lines 99-106)
    if line_num >= 99 and line_num <= 106:
        if line_num == 99:
            # Replace with the correct code
            fixed_lines.append("        programmes = db_service.list_programmes()\n")
        # Skip all other corrupted lines
        continue
    else:
        fixed_lines.append(line)

# Write back
with open('/Users/berntblankholm/efmd-gap-tool/frontend/app.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed app.py - removed corrupted lines 100-106 and fixed line 99")
