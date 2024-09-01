import os

examples = os.listdir("./examples/")

examples = list(filter(lambda ex: ':'not in ex, examples))

for ex in examples:
  print("File: " + ex)
  os.system("python3 inv_mc.py examples/" + ex)
  print()