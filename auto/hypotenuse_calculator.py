def calculate_hypotenuse(a, b):
    """Calculates the hypotenuse of a right triangle given sides a and b.

    Args:
        a (float): Length of side a.
        b (float): Length of side b.

    Returns:
        float: The length of the hypotenuse.
    """
    # Calculate the hypotenuse
    hypotenuse = (a**2 + b**2)**0.5
    return hypotenuse

# Example usage
if __name__ == '__main__':
    a = 3
    b = 4
    hypotenuse = calculate_hypotenuse(a, b)
    print(f'The hypotenuse of a right triangle with sides {a} and {b} is {hypotenuse}.')