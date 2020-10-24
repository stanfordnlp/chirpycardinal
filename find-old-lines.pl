#!/usr/bin/perl

# This script parses Git blame's "porcelain" output format and
# ascertains the oldest lines of code seen.
#
# If you want to perform a custom report, just define your own callback
# function and invoke parse_porcelain() with it.
#
# The expected input format is slightly modified from raw `git blame
# -p`. Here is an example script for producing input:
#
# for f in `git ls-tree -r --name-only HEAD`; do \
#   echo "BEGIN_RECORD $f"; \
#   git blame -l -t -M -C -n -w -p $f; \
#   echo "END_RECORD $f"; \
# done

use strict;
use warnings FATAL => "all";

use POSIX qw(strftime);

our @STATES = qw(global header_first header_metadata);

our $RE_BEGIN_RECORD = qr/^BEGIN_RECORD\s(.*)$/msx;
our $RE_END_RECORD = qr/^END_RECORD\s(.*)$/msx;

our $RE_LINE_HEADER = qr/
  ^
  ([a-z0-9]{40}) # SHA
  \s(\d+)        # Original line number
  \s(\d+)        # Current line number
  (?:\s(\d+))?   # Number of lines in group (optional)
  $/msx;

our $RE_HEADER_METADATA = qr/^([a-z-]+)\s(.*)$/msx;
our $RE_LINE_DATA = qr/^\t(.*)$/msx;

# Parses Git blame's porcelain output.
# Calls the supplied $onBlock callback function when a full block of
# code has been parsed. The function receives a hashref describing the
# block.
sub parse_porcelain {
  my ($fh, $onBlock) = @_;

  my $state = "global";
  my $metadata = {};
  my @lines;
  my ($commit, $original_line, $current_line);
  my $current_file;

  my $callOnBlock = sub {
    my $data = {};
    $data->{'filename'} = $current_file;
    $data->{'lines'} = \@lines;
    $data->{'metadata'} = $metadata;
    $data->{'commit'} = $commit;

    &$onBlock($data);

    @lines = ();
  };

  while (my $line = <$fh>) {
    chomp $line;

    if ($line =~ $RE_BEGIN_RECORD) {
      $state eq "global" or die "Parser error. Unexpected BEGIN_RECORD.";

      $current_file = $1;
      $state = "header_first";

      next;
    }
    elsif ($line =~ $RE_END_RECORD) {
      $1 eq $current_file or die "Parser error. END_RECORD mismatch!";

      if ($onBlock and scalar(@lines)) {
        &$callOnBlock();
      }

      $state = "global";
      next;
    }

    if ($state eq "header_first") {
      $line =~ $RE_LINE_HEADER or die "Invalid initial header line! $line";
      my ($new_commit, $new_original_line, $new_current_line, $block_count);
      ($new_commit, $new_original_line, $new_current_line, $block_count) = ($1, $2, $3, $4);

      if ($block_count and $onBlock and scalar(@lines)) {
        &$callOnBlock();
      }

      $commit = $new_commit;
      $original_line = $new_original_line;
      $current_line = $new_current_line;

      $state = "header_metadata";
      next;
    }

    if ($state eq "header_metadata") {
      # Lines beginning with a tab denote line content. Subsequent line(s)
      # will be metadata for that line.
      if ($line =~ $RE_LINE_DATA) {
        my $content = $1;

        push @lines, [$content, $original_line, $current_line];
        $state = "header_first";
        next;
      }

      next if $line eq "boundary";

      $line =~ $RE_HEADER_METADATA or die "Could not parse header metadata.";
      my ($k, $v) = ($1, $2);

      $metadata->{$k} = $v;
      next;
    }

    die "Unknown state!";
  }
}

# onBlock callback that collects oldest commit times for blocks.
my $old_lines = {};
sub collect_times {
  my ($data) = @_;

  # We filter non-relevant lines.
  my $have_content = 0;

  foreach my $line (@{$data->{'lines'}}) {
    my $s = $line->[0];

    # Skip empty and whitespace.
    next if $s =~ m/^\s*$/;

    # Skip things looking like comments.
    next if $s =~ m/^\s*(#|\/\/|\/\*|\*\/)/;

    if ($s =~ m/[a-z0-9]/) {
      $have_content = 1;
      last;
    }
  }

  if (!$have_content) {
    return;
  }

  my $time = $data->{'metadata'}->{'committer-time'};

  my $metadata = {};
  $metadata->{'commit'} = $data->{'commit'};
  $metadata->{'author'} = $data->{'metadata'}->{'author'};
  $metadata->{'filename'} = $data->{'filename'};
  $metadata->{'lines'} = [];

  foreach my $line (@{$data->{'lines'}}) {
    push @{$metadata->{'lines'}}, $line->[2];
  }

  push @{$old_lines->{$time}}, $metadata;
}

sub print_oldest_blocks {
  my ($times) = @_;

  foreach my $time (sort { $a <=> $b } keys %$times) {
    my $blocks = $times->{$time};
    my $date = strftime("%Y-%m-%d %H:%M:%S", gmtime($time));

    print "Time: $time ($date)\n";
    foreach my $data (@$blocks) {
      print "  Commit: " . $data->{'commit'} . "\n";
      print "    Author: " . $data->{'author'} . "\n";
      print "    Filename: " . $data->{'filename'} . "\n";
      print "    Lines: " . join(', ', @{$data->{'lines'}}) . "\n";
    }
  }
}

parse_porcelain(*STDIN, \&collect_times);
print_oldest_blocks($old_lines);
