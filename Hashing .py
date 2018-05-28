try:
    import hashlib
except:
    print("erreur")

##print(hashlib.algorithms_available)
##print(hashlib.algorithms_guaranteed)
    
hash_object = hashlib.md5(b'Hello World')
print(hash_object.hexdigest())

mystring = input('Enter String to hash: ')
# Assumes the default UTF-8
hash_object = hashlib.md5(mystring.encode())
print(hash_object.hexdigest())