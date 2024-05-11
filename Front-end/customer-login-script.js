AWS.config.region = 'eu-central-1'; // Specify your AWS region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: 'eu-central-1_HWPGNhtNT' // Specify your Cognito Identity Pool ID
});

var cognitoIdentity = new AWS.CognitoIdentity();
var cognitoUser;

document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault();
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    var authenticationData = {
        Username: username,
        Password: password
    };

    var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);

    var poolData = {
        UserPoolId: 'eu-central-1_HWPGNhtNT', // Specify your User Pool ID
        ClientId: '41f585j60sudk6kgegu3h3gks6' // Specify your App Client ID
    };

    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

    var userData = {
        Username: username,
        Pool: userPool
    };

    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: function (result) {
            // Authentication successful
            console.log('Authentication successful');
            console.log('Access token: ' + result.getAccessToken().getJwtToken());
            console.log('ID token: ' + result.getIdToken().getJwtToken());
            // Store the token in localStorage
            localStorage.setItem('cognito_id_token', result.getIdToken().getJwtToken());
            // Redirect to Feedback Form
            window.location.href = "customer-feedback.html";
        },
        onFailure: function(err) {
            // Authentication failed
            console.log('Authentication failed');
            document.getElementById("error-message").innerText = err.message || JSON.stringify(err);
        },
        newPasswordRequired: function(userAttributes, requiredAttributes) {
            // User needs to set a new password
            console.log('New password required');
            // Handle new password scenario
            // You can redirect the user to a page where they can set a new password
        }
    });
});
