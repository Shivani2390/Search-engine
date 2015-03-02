#!/bin/bash
gunzip -c input.gz | dd bs=65536 skip=0 count=1 >'cache.txt'