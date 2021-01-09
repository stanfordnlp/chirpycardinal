#!/bin/sh
num_files=`git ls-tree -r --name-only HEAD | wc -l`
i=0
for f in `git ls-tree -r --name-only HEAD`; do \
  i=$((i+1))
  printf "%d/%d %s\r" $i $num_files $f > /dev/tty
  echo "BEGIN_RECORD $f"; \
  git blame -l -t -M -C -n -w -p $f; \
  echo "END_RECORD $f"; \
done | ./find-old-lines.pl
