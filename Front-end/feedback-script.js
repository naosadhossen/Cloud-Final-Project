document.getElementById("review-form").addEventListener("submit", function(event) {
    event.preventDefault();
    var reviewText = document.getElementById("review-text").value;

    // Get the JWT token from local storage
    var idToken = localStorage.getItem('cognito_id_token');

    if (!idToken) {
        console.error('No token available');
        return;
    }

    var apiUrl = 'https://5vfm97o7vk.execute-api.eu-central-1.amazonaws.com/default/lambda-feedback';

    var xhr = new XMLHttpRequest();
    xhr.open('POST', apiUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', idToken);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                console.log('Review submitted successfully');
                var response = JSON.parse(xhr.responseText);
                document.getElementById('response-message').textContent = response.message;
                // Optionally, you can redirect the user or display a success message
            } else {
                console.error('Failed to submit review:', xhr.responseText);
                var errorResponse = JSON.parse(xhr.responseText);
                document.getElementById('response-message').textContent = 'Error: ' + errorResponse.message; //
                // Optionally, you can display an error message to the user
            }
        }
    };

    var data = JSON.stringify({
        text: reviewText
    });

    xhr.send(data);
});
