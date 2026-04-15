release:
    git push
    git switch release
    git merge main
    git push
    git switch main

testfiles:
    python -c "from tests.test_cleaner import setup_test; setup_test()"
