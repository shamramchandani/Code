inventory = {'rope': 1, 'torch': 6, 'gold coin': 42, 'dagger': 1, 'arrow': 12}

def displayInventory(inventory):
  print('Inventory: ')
  
  totalItems = 0
  
  for key, value in inventory.items():
    print(str(value) + ' ' + key)
    totalItems += value
  
  print('Total number of items: ' + str(totalItems))

displayInventory(inventory)