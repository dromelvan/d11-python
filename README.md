# d11-python
Python stuff for adminstration and updating for the D11 application

To install packages and run do:

make
source venv/bin/activate

To leave the virtual environment:

deactivate

To use any Selenium functions do:

brew install geckodriver

Run a Firefox version that works with latest geckodriver, presumably the lastest Firefox version.
Create a new profile in Firefox and navigate to Fotmob using that profile to click away all the consent popups once.
Update FOTMOB_SELENIUM_PROFILE_PATH property in .env with the path to this profile.