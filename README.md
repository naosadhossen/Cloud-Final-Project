# Cloud-FInal-Project
## lambda-review
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

### Create a .env file (Mac): 
touch .env   

Populate the .env file with following variables according to your actual project setup. 
AWS_REGION_NAME=  
TABLE_NAME=  
GOOGLE_NLP_API_KEY=  
TWILIO_ACCOUNT_SID=  
TWILIO_AUTH_TOKEN=  
TWILIO_MAX_TRY_ATTEMPTS=  
TWILIO_DELAY_SEC=  
TWILIO_FROM=  

### Make a Zip package for Lambda:  
cd package  
zip -r ../lambda_function.zip .  
cd ..  
zip lambda_function.zip lambda_function.py  
zip lambda_function.zip .env  


