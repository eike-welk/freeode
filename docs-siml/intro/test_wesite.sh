#Build the website and test it
set -e
make html
firefox _build/html/index.html
