#!/bin/bash

for file in ./chirpy/response_generators/wiki/*
do
  echo "$file"
  if [ -f $file ]
    then 
      if [ ${file: -3} == ".py" ]
        then
        python -m doctest "$file"
      fi
  fi
done

for file in ./chirpy/response_generators/wiki/*/*
do
  echo "$file"
  if [ -f $file ]
    then 
      if [ ${file: -3} == ".py" ]
        then
        python -m doctest "$file"
      fi
  fi
done