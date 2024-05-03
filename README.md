# cloud-final
## Feedback
### Execute in commandline (Mac):  
mkdir package  
pip install \  
--platform manylinux2014_x86_64 \  
--target=package \  
--implementation cp \  
--python-version 3.9 \  
--only-binary=:all: --upgrade \  
python-dotenv requests twilio  
Now all the 3rd party packages are installed in package folder
