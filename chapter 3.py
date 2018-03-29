def collatz(num):
   if num%2 == 0:
     print(num / 2)
     return (num / 2)
   else:
     print((num *3) +1)
     return (num *3) +1
     

try:
  number = int(input("Please enter a number"))
  print(number)
  if number <= 1:
    print('Please input a number greater than 1')
  else:
    while number > 1:
      number = collatz(number)
except (NameError, ValueError):
  print('Error: Please Enter a Number')