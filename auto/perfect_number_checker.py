def is_perfect_number(number):
    # Initialize the sum of divisors
    sum_of_divisors = 0

    # Iterate over all possible divisors
    for i in range(1, number):
        if number % i == 0:
            sum_of_divisors += i

    # Compare the sum of divisors with the original number
    if sum_of_divisors == number:
        return True
    else:
        return False

if __name__ == '__main__':
    # Take user input
    num = int(input("Enter an integer to check if it is a perfect number: "))

    # Check if the number is perfect
    if is_perfect_number(num):
        print(f"{num} is a perfect number.")
    else:
        print(f"{num} is not a perfect number.")
