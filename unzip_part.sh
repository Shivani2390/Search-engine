#!/bin/bash
#echo 'First'
#echo $1
#echo 'Second'
#echo $2
#echo $3
val1=$(( $1 + 0))
val2=$(( $2 + 0)) 
gunzip -c input.gz | dd bs=$val1 skip=$val2 count=2 >$3