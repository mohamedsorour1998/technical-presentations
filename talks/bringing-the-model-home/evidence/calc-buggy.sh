#!/bin/bash

# calc.sh - Basic calculator script
# Usage: ./calc.sh <number1> <operator> <number2>
# Operators: + - x /

if [ $# -ne 3 ]; then
    echo "Usage: $0 <number> <operator> <number>"
    echo "Operators: + - x /"
    exit 1
fi

num1=$1
op=$2
num2=$3

result=$(awk "BEGIN { print $num1 $op $num2 }")

echo $result
