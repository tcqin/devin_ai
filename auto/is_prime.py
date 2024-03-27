def is_prime(number):
    """Check if a number is prime.
    
    Args:
        number (int): The number to check.
    
    Returns:
        bool: True if the number is prime, otherwise False.
    """
    if number <= 1:
        return False
    for i in range(2, int(number**0.5) + 1):
        if number % i == 0:
            return False
    return True
