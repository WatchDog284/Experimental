#include <cs50.h>
#include <stdio.h>

bool check_luhn(long number);
int get_length(long number);
void check_card_type(long number);

int main(void)
{
    long card_number;

    // Prompt user for credit card number using a do-while loop
    do
    {
        card_number = get_long("Number: ");
    } while (card_number <= 0);

    // Validate card number using Luhn's Algorithm
    if (check_luhn(card_number))
    {
        // Check and print card type
        check_card_type(card_number);
    }
    else
    {
        printf("INVALID\n");
    }
}


// Function to validate card number using Luhn's Algorithm
bool check_luhn(long number)
{
    int sum = 0;
    bool alternate = false;

    while (number > 0)
    {
        int digit = number % 10;
        if (alternate)
        {
            digit *= 2;
            if (digit > 9)
            {
                digit -= 9;
            }
        }
        sum += digit;
        alternate = !alternate;
        number /= 10;
    }

    return (sum % 10) == 0;
}

// Function to get the length of the card number
int get_length(long number)
{
    int length = 0;
    while (number > 0)
    {
        number /= 10;
        length++;
    }
    return length;
}

// Function to check and print the card type
void check_card_type(long number)
{
    int length = get_length(number);
    int start_digits = number;

    // Get the first two digits
    while (start_digits >= 100)
    {
        start_digits /= 10;
    }

    if ((length == 13 || length == 16) && (start_digits / 10 == 4))
    {
        printf("VISA\n");
    }
    else if (length == 15 && (start_digits == 34 || start_digits == 37))
    {
        printf("AMEX\n");
    }
    else if (length == 16 && (start_digits >= 51 && start_digits <= 55))
    {
        printf("MASTERCARD\n");
    }
    else
    {
        printf("INVALID\n");
    }
}