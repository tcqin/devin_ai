def is_prime(n):
    """Determine if a number is prime."""
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

if __name__ == '__main__':
    number = int(input("Enter a positive integer: "))
    if number <= 0:
        print("Please enter a positive integer.")
    else:
        if is_prime(number):
            print(f"{number} is a prime number.")
        else:
            print(f"{number} is not a prime number.")