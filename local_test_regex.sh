# This command searches recursively through the chirpy/ directory,
# and runs all unittests that can be discovered in any *.py file.
# Currently, this means it runs all the RegexTemplate tests.
# Note it does not run the integration tests, because those are in test/ not chirpy/

# IMPORTANT: python -m unittest discover says:
# "For test discovery all test modules must be importable from the top level
# directory of the project."
# If your test isn't showing up, it may be because it isn't in an importable
# module. Try adding an __init__.py file. b

python -m unittest discover -s chirpy -p '*.py' -v

# There is a known problem that tests run multiple times; it seems that there
# are several possible reasons why:
# https://www.google.com/search?q=unittest+tests+run+twice&rlz=1C5CHFA_enUS878US878&oq=unittest+tests+run+twice&aqs=chrome..69i57j33l3.5474j1j7&sourceid=chrome&ie=UTF-8
# I (Abi) am not sure how to fix it, and it seems that all our tests are being
# run, so I'm leaving it as-is.
