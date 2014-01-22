import hashlib
from base64 import b64encode

with open('C:\\Users\\crosie\\Desktop\\new_dl\\0bb2e1a7-d5fd-49dd-b480-8f4deb61e82a.xml', 'r') as f:
	contents = f.read()

	h = hashlib.sha1()
	h.update(contents)
	file_hash = h.digest()
	print "Hash: ", file_hash

	encoded = b64encode(file_hash)

	print "Expected: CrNTnlbbPQoowcRK0gvZ9FYrnFM="
	print "Actual: ", encoded
