#!/bin/sh

grep MASTER $1 | awk '{ print $4, $5, $6, $7, $8, $9}' 
