#include <stdio.h>
#include <cs50.h>

// Function prototypes
bool check_sum(long card_number); // Function to validate card number using Luhn's algorithm
int get_length(long card_number); // Function to calculate the length of the card number

int main(void)
{
    // Prompt user for card number
    long card_number = get_long("Number: ");
    
    // Check if the card number passes Luhn's algorithm
    if (!check_sum(card_number))
    {
        printf("INVALID\n");
        return 0; // Exit if the card number is invalid
    }
    else
    {
        // Get the length of the card number
        int length = get_length(card_number);
        
        // Extract the starting digits of the card number
        long temp_card_number = card_number;
        int start_digits = 0;
        while (temp_card_number >= 100) // Reduce to the first two digits
        {
            temp_card_number /= 10;
        }
        start_digits = temp_card_number;

        // Determine the card type based on length and starting digits
        if ((length == 13 || length == 16) && (start_digits / 10 == 4))
        {
            printf("VISA\n"); // VISA cards start with 4 and have 13 or 16 digits
        }
        else if (length == 15 && (start_digits == 34 || start_digits == 37))
        {
            printf("AMEX\n"); // AMEX cards start with 34 or 37 and have 15 digits
        }
        else if (length == 16 && (start_digits >= 51 && start_digits <= 55))
        {
            printf("MASTERCARD\n"); // MASTERCARD cards start with 51-55 and have 16 digits
        }
        else
        {
            printf("INVALID\n"); // If none of the conditions match, the card is invalid
        }
    }
}

// Function to validate the card number using Luhn's algorithm
bool check_sum(long card_number)
{
    int sum = 0;
    bool alternate = false; // Flag to alternate between digits

    while (card_number > 0)
    {
        int digit = card_number % 10; // Extract the last digit
        if (alternate)
        {
            digit *= 2; // Double every second digit
            if (digit > 9)
            {
                digit -= 9; // Subtract 9 if the result is greater than 9
            }
        }
        sum += digit; // Add the digit to the sum
        alternate = !alternate; // Toggle the alternate flag
        card_number /= 10; // Remove the last digit
    }
    return (sum % 10) == 0; // Return true if the sum is divisible by 10
}

// Function to calculate the length of the card number
int get_length(long card_number)
{
    int length = 0;
    while (card_number > 0)
    {
        card_number /= 10; // Remove the last digit
        length++; // Increment the length counter
    }
    return length; // Return the total length
}
