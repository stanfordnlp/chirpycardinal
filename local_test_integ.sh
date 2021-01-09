# This command runs all integration tests, and saves the output to integ_test_results.txt.

# Nosetests prints to stderr. 2>&1 reroutes stderr to stdout.
# "| tee" writes stdout to file, while also showing stdout in terminal.

# See the "integration testing" internal documentation to see how to change
# the nosetests command to just run particular tests.

nosetests -v test/integration_tests/*.py 2>&1 | tee integ_test_results.txt

# Print out list of failed tests for convenience
echo '\nList of failed tests (might be empty):'
grep '... FAIL' integ_test_results.txt
grep '... ERROR' integ_test_results.txt

echo '\nSee integ_test_results.txt for full report'
