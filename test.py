# import time
# import sys

count = 1
print('good')
while count < 99:
    sys.stdout.write("current {}  {}%\r".format('#'*count,count))
    sys.stdout.flush()
    count += 1
    time.sleep(0.5)