import subprocess

# Combine all the inputs as a single bytes object
inputs = b"2025\n90\n200.8\nyes\n4000\n0\n0\n40\n0\n0\n2000\n3000\n0\n0\n0\n0\nno\n10\n500\n0\n0\n0\n0\n"

p = subprocess.Popen(
    "python C:\\Users\\Lenovo\\Desktop\\skatouts9\\maritime_optimization\\code\\optimize2.py", 
    shell=True, 
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Send all the inputs at once
stdO, stdE = p.communicate(inputs)

# Attempt to decode the output, handle potential errors
try:
    print(stdO.decode('utf-8'))
except UnicodeDecodeError:
    print("Output contains non-utf-8 bytes. Printing raw output:")
    print(stdO)

try:
    print(stdE.decode('utf-8'))
except UnicodeDecodeError:
    print("Error output contains non-utf-8 bytes. Printing raw error output:")
    print(stdE)
