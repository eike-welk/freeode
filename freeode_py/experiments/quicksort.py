'''
Created on May 16, 2010

@author: Eike Welk
'''

def quicksort(in_list):
    '''Recursive quicksort algorithm'''
    #empty lists don't need to be sorted (stop recursion)
    if len(in_list) == 0:
        return in_list
    
    #pivot is compared to the rest of the list
    pivot = in_list[0]
    rest_list = in_list[1:]
    #Build two sublists: elements in first list are all smaller than pivot,
    # elements in second list are all bigger. sort the sublists.
    front_list = quicksort([front for front in rest_list if front < pivot])
    back_list =  quicksort([back  for back  in rest_list if back >= pivot])
    #reassemble into complete list
    return front_list + [pivot] + back_list


    
if __name__ == '__main__':
    print quicksort([])
    print quicksort([2,1,5,3])
    
    sorted_list = range(0,100)
    reversed_list = sorted_list[::-1]
    assert quicksort(reversed_list) == sorted_list
    