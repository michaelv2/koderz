import hashlib

def string_to_md5(text):
    if text == "":
        return None
    else:
        # Create an md5 hash object
        m = hashlib.md5()
        
        # Update the hash object with the bytes of the input string
        m.update(text.encode('utf-8'))
        
        # Return the hexadecimal representation of the digest
        return m.hexdigest()